"""
Ollama setup and configuration utilities.
"""

import argparse
import json
import subprocess
import sys
import time
from pathlib import Path
from typing import List, Optional

import requests


class OllamaSetup:
    """Setup and configuration for Ollama."""

    def __init__(self) -> None:
        self.base_url = "http://localhost:11434"
        self.recommended_models = {
            "qwen3:8b": {
                "size": "4.7GB",
                "description": "Qwen3 8B model, excellent for text processing",
                "strengths": ["Text analysis", "JSON output", "Academic content"],
                "recommended": True,
            },
            "qwen2.5:32b-instruct-q4_K_M": {
                "size": "19GB",
                "description": "High-quality model with excellent JSON output",
                "strengths": [
                    "Perfect JSON",
                    "Academic analysis",
                    "Keyword extraction",
                ],
                "recommended": True,
            },
            "qwen2:72b": {
                "size": "40GB",
                "description": "Large model with superior reasoning",
                "strengths": [
                    "Complex reasoning",
                    "High accuracy",
                    "Detailed analysis",
                ],
                "recommended": False,
            },
            "mistral": {
                "size": "4.1GB",
                "description": "Fast and efficient model for text processing",
                "strengths": ["Speed", "Efficiency", "Good JSON output"],
                "recommended": False,
            },
        }

    def check_ollama_installed(self) -> bool:
        """Check if Ollama is installed."""
        try:
            result = subprocess.run(
                ["ollama", "--version"], capture_output=True, text=True, timeout=10
            )
            if result.returncode == 0:
                print(f"✅ Ollama is installed: {result.stdout.strip()}")
                return True
            else:
                print("❌ Ollama command failed")
                return False
        except FileNotFoundError:
            print("❌ Ollama not found in PATH")
            return False
        except subprocess.TimeoutExpired:
            print("❌ Ollama command timed out")
            return False
        except Exception as e:
            print(f"❌ Error checking Ollama: {e}")
            return False

    def check_ollama_running(self) -> bool:
        """Check if Ollama service is running."""
        try:
            response = requests.get(f"{self.base_url}/api/tags", timeout=5)
            if response.status_code == 200:
                print("✅ Ollama service is running")
                return True
            else:
                print(f"❌ Ollama service returned status {response.status_code}")
                return False
        except requests.exceptions.ConnectionError:
            print("❌ Ollama service is not running")
            return False
        except Exception as e:
            print(f"❌ Error checking Ollama service: {e}")
            return False

    def get_installed_models(self) -> List[str]:
        """Get list of installed models."""
        try:
            response = requests.get(f"{self.base_url}/api/tags", timeout=10)
            if response.status_code == 200:
                data = response.json()
                models = [model["name"] for model in data.get("models", [])]
                return models
            else:
                print(f"❌ Failed to get models: status {response.status_code}")
                return []
        except Exception as e:
            print(f"❌ Error getting models: {e}")
            return []

    def install_model(self, model_name: str) -> bool:
        """Install a specific model."""
        print(f"📥 Installing model: {model_name}")

        if model_name in self.recommended_models:
            model_info = self.recommended_models[model_name]
            print(f"   Size: {model_info['size']}")
            print(f"   Description: {model_info['description']}")

        try:
            # Use ollama pull command
            process = subprocess.Popen(
                ["ollama", "pull", model_name],
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                bufsize=1,
                universal_newlines=True,
            )

            print("   Progress:")
            if process.stdout:
                while True:
                    output = process.stdout.readline()
                    if output == "" and process.poll() is not None:
                        break
                if output:
                    # Clean up progress output
                    line = output.strip()
                    if line and not line.startswith(
                        "\x1b"
                    ):  # Skip ANSI escape sequences
                        print(f"   {line}")

            return_code = process.poll()

            if return_code == 0:
                print(f"✅ Successfully installed {model_name}")
                return True
            else:
                print(f"❌ Failed to install {model_name} (exit code: {return_code})")
                return False

        except Exception as e:
            print(f"❌ Error installing {model_name}: {e}")
            return False

    def test_model(self, model_name: str) -> bool:
        """Test if a model works correctly."""
        print(f"🧪 Testing model: {model_name}")

        test_prompt = (
            'Extract keywords from this text: "Catalytic conversion of '
            'nitrogen oxides to ammonia using electrochemical methods."\n\n'
            'Return JSON format: {"keywords": ["keyword1", "keyword2"]}'
        )

        try:
            payload = {
                "model": model_name,
                "prompt": test_prompt,
                "stream": False,
                "options": {"temperature": 0.1, "num_ctx": 2048},
            }

            response = requests.post(
                f"{self.base_url}/api/generate", json=payload, timeout=30
            )

            if response.status_code == 200:
                result = response.json()
                output = result.get("response", "").strip()

                # Try to parse as JSON
                try:
                    parsed = json.loads(output)
                    if "keywords" in parsed and isinstance(parsed["keywords"], list):
                        print(f"✅ Model {model_name} works correctly")
                        print(f"   Test output: {parsed['keywords']}")
                        return True
                    else:
                        print(
                            f"⚠ Model {model_name} works but output format "
                            "needs improvement"
                        )
                        return True
                except json.JSONDecodeError:
                    print(f"⚠ Model {model_name} works but doesn't return valid JSON")
                    print(f"   Raw output: {output[:100]}...")
                    return True
            else:
                print(f"❌ Model test failed: status {response.status_code}")
                return False

        except Exception as e:
            print(f"❌ Error testing model: {e}")
            return False

    def recommend_model(self) -> str:
        """Recommend the best model for the user's system."""
        print("🤔 Analyzing system for model recommendation...")

        # Check available disk space (simplified)
        try:
            import shutil

            free_space = shutil.disk_usage(Path.home()).free / (1024**3)  # GB
            print(f"   Available disk space: {free_space:.1f} GB")

            if free_space < 5:
                print("⚠ Low disk space detected - recommending smaller model")
                return "qwen3:8b"
            elif free_space > 25:
                print("✅ Sufficient disk space for large models")
                return "qwen2.5:32b-instruct-q4_K_M"
            else:
                print("✅ Sufficient disk space for medium models")
                return "qwen3:8b"

        except Exception:
            print("   Could not determine disk space")
            return "qwen3:8b"

    def print_model_info(self) -> None:
        """Print information about available models."""
        print("\n📋 Available Models for PDF Processing:")
        print("=" * 60)

        for model_name, info in self.recommended_models.items():
            status = "⭐ RECOMMENDED" if info["recommended"] else "  Alternative"
            print(f"\n{status} {model_name}")
            print(f"   Size: {info['size']}")
            print(f"   Description: {info['description']}")
            strengths = info.get("strengths", [])
            if isinstance(strengths, list):
                print(f"   Strengths: {', '.join(strengths)}")

    def setup_complete_system(self, model_name: Optional[str] = None) -> bool:
        """Complete setup process."""
        print("🚀 Setting up Ollama for PDF processing...")

        # Step 1: Check Ollama installation
        if not self.check_ollama_installed():
            print("\n❌ Ollama is not installed. Please install it first:")
            print("   macOS: brew install ollama")
            print("   Linux: curl -fsSL https://ollama.ai/install.sh | sh")
            print("   Windows: Download from https://ollama.ai/download")
            return False

        # Step 2: Check if service is running
        if not self.check_ollama_running():
            print("\n🔄 Starting Ollama service...")
            try:
                subprocess.Popen(
                    ["ollama", "serve"],
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL,
                )
                time.sleep(3)  # Give it time to start

                if not self.check_ollama_running():
                    print("❌ Failed to start Ollama service")
                    print("   Try running 'ollama serve' manually in another terminal")
                    return False
            except Exception as e:
                print(f"❌ Error starting Ollama: {e}")
                return False

        # Step 3: Check installed models
        installed_models = self.get_installed_models()
        print(
            f"\n📦 Installed models: {installed_models if installed_models else 'None'}"
        )

        # Step 4: Determine which model to install
        if not model_name:
            model_name = self.recommend_model()

        # Check if model is already installed
        model_installed = any(model_name in installed for installed in installed_models)

        if model_installed:
            print(f"✅ Model {model_name} is already installed")
        else:
            # Step 5: Install recommended model
            if not self.install_model(model_name):
                return False

        # Step 6: Test the model
        if not self.test_model(model_name):
            print("⚠ Model test had issues, but installation appears successful")

        print(f"\n🎉 Setup complete! You can now use model: {model_name}")
        print("\nNext steps:")
        print("1. Test PDF processing:")
        print(f"   ai-pdf-extract extract your_paper.pdf --model {model_name}")
        print("2. Update knowledge index:")
        print("   ai-pdf-extract knowledge --stats")

        return True


def main() -> None:
    """Command-line interface for Ollama setup."""
    parser = argparse.ArgumentParser(description="Setup Ollama for PDF processing")
    parser.add_argument(
        "--model", help="Specific model to install (default: auto-recommend)"
    )
    parser.add_argument(
        "--check-only",
        action="store_true",
        help="Only check current status, don't install anything",
    )
    parser.add_argument(
        "--list-models",
        action="store_true",
        help="List available models and their information",
    )

    args = parser.parse_args()

    setup = OllamaSetup()

    if args.list_models:
        setup.print_model_info()
        return

    if args.check_only:
        print("🔍 Checking Ollama status...")

        installed = setup.check_ollama_installed()
        running = setup.check_ollama_running() if installed else False
        models = setup.get_installed_models() if running else []

        print("\n📊 Status Summary:")
        print(f"   Ollama installed: {'✅' if installed else '❌'}")
        print(f"   Service running: {'✅' if running else '❌'}")
        print(f"   Models available: {len(models)}")

        if models:
            print(f"   Installed models: {', '.join(models[:5])}")
            if len(models) > 5:
                print(f"   ... and {len(models) - 5} more")

        return

    # Full setup
    success = setup.setup_complete_system(args.model)

    if not success:
        print("\n💥 Setup failed. Please check the errors above.")
        sys.exit(1)


if __name__ == "__main__":
    main()
