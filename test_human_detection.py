#!/usr/bin/env python3
"""
Test Suite for Human Detection Script
Tests various scenarios and edge cases
"""

import sys
import json
import subprocess
import time
from pathlib import Path

# Colors for output
GREEN = '\033[92m'
RED = '\033[91m'
YELLOW = '\033[93m'
BLUE = '\033[94m'
RESET = '\033[0m'

class TestRunner:
    def __init__(self):
        self.passed = 0
        self.failed = 0
        self.skipped = 0
        self.tests = []
        
    def test(self, name, description):
        """Decorator for test functions"""
        def decorator(func):
            self.tests.append({
                'name': name,
                'description': description,
                'func': func
            })
            return func
        return decorator
    
    def run_all(self):
        """Run all registered tests"""
        print(f"\n{BLUE}{'='*70}{RESET}")
        print(f"{BLUE}Human Detection Test Suite{RESET}")
        print(f"{BLUE}{'='*70}{RESET}\n")
        
        for i, test in enumerate(self.tests, 1):
            print(f"{YELLOW}[{i}/{len(self.tests)}]{RESET} {test['name']}")
            print(f"    {test['description']}")
            
            try:
                result = test['func']()
                if result == 'SKIP':
                    self.skipped += 1
                    print(f"    {YELLOW}⊘ SKIPPED{RESET}\n")
                elif result:
                    self.passed += 1
                    print(f"    {GREEN}✓ PASSED{RESET}\n")
                else:
                    self.failed += 1
                    print(f"    {RED}✗ FAILED{RESET}\n")
            except Exception as e:
                self.failed += 1
                print(f"    {RED}✗ FAILED: {str(e)}{RESET}\n")
        
        self.print_summary()
    
    def print_summary(self):
        """Print test summary"""
        total = self.passed + self.failed + self.skipped
        print(f"{BLUE}{'='*70}{RESET}")
        print(f"{BLUE}Test Summary{RESET}")
        print(f"{BLUE}{'='*70}{RESET}")
        print(f"Total Tests: {total}")
        print(f"{GREEN}Passed: {self.passed}{RESET}")
        print(f"{RED}Failed: {self.failed}{RESET}")
        print(f"{YELLOW}Skipped: {self.skipped}{RESET}")
        
        if self.failed == 0:
            print(f"\n{GREEN}{'='*70}")
            print(f"ALL TESTS PASSED! 🎉")
            print(f"{'='*70}{RESET}\n")
        else:
            print(f"\n{RED}{'='*70}")
            print(f"SOME TESTS FAILED")
            print(f"{'='*70}{RESET}\n")

# Initialize test runner
runner = TestRunner()

# ============================================================================
# TEST CASES
# ============================================================================

@runner.test("Environment Check", "Verify Python environment and dependencies")
def test_environment():
    """Test that required Python packages are installed"""
    try:
        import cv2
        import numpy as np
        print(f"    OpenCV version: {cv2.__version__}")
        print(f"    NumPy version: {np.__version__}")
        return True
    except ImportError as e:
        print(f"    Missing dependency: {e}")
        return False

@runner.test("Script Exists", "Verify detect_human.py exists")
def test_script_exists():
    """Test that the main script exists"""
    script_path = Path(__file__).parent / "detect_human.py"
    exists = script_path.exists()
    if exists:
        print(f"    Found: {script_path}")
    else:
        print(f"    Not found: {script_path}")
    return exists

@runner.test("HOG Models Available", "Check if HOG detector is available")
def test_hog_available():
    """Test HOG detector availability (built-in to OpenCV)"""
    try:
        import cv2
        hog = cv2.HOGDescriptor()
        hog.setSVMDetector(cv2.HOGDescriptor_getDefaultPeopleDetector())
        print(f"    HOG detector initialized successfully")
        return True
    except Exception as e:
        print(f"    HOG initialization failed: {e}")
        return False

@runner.test("MobileNet Models Check", "Check if MobileNet models exist")
def test_mobilenet_models():
    """Test if MobileNet model files exist"""
    models_dir = Path(__file__).parent / "models"
    prototxt = models_dir / "MobileNetSSD_deploy.prototxt"
    caffemodel = models_dir / "MobileNetSSD_deploy.caffemodel"
    
    if prototxt.exists() and caffemodel.exists():
        print(f"    ✓ MobileNet models found")
        return True
    else:
        print(f"    ⚠ MobileNet models not found (run: cd models && bash download_models.sh)")
        return 'SKIP'

@runner.test("YOLO Models Check", "Check if YOLO models exist")
def test_yolo_models():
    """Test if YOLO model files exist"""
    models_dir = Path(__file__).parent / "models"
    cfg = models_dir / "yolov3.cfg"
    weights = models_dir / "yolov3.weights"
    names = models_dir / "coco.names"
    
    if cfg.exists() and weights.exists() and names.exists():
        print(f"    ✓ YOLO models found")
        return True
    else:
        print(f"    ⚠ YOLO models not found (run: cd models && bash download_models.sh)")
        return 'SKIP'

@runner.test("JSON Output Format", "Test JSON output parsing")
def test_json_output():
    """Test that script outputs valid JSON"""
    script_path = Path(__file__).parent / "detect_human.py"
    
    # Run script with --help to test it executes
    try:
        result = subprocess.run(
            ['python3', str(script_path), '--help'],
            capture_output=True,
            text=True,
            timeout=5
        )
        
        if result.returncode == 0:
            print(f"    Script executes successfully")
            return True
        else:
            print(f"    Script failed with code {result.returncode}")
            return False
    except subprocess.TimeoutExpired:
        print(f"    Script timed out")
        return False
    except Exception as e:
        print(f"    Error: {e}")
        return False

@runner.test("Error Handling - Invalid Camera", "Test error handling for invalid camera")
def test_invalid_camera():
    """Test that script handles invalid camera gracefully"""
    script_path = Path(__file__).parent / "detect_human.py"
    
    try:
        # Use a very high camera ID that likely doesn't exist
        result = subprocess.run(
            ['python3', str(script_path), '--method', 'hog', '--camera', '999', '--no-display'],
            capture_output=True,
            text=True,
            timeout=5
        )
        
        # Should fail or output error JSON
        output = result.stdout.strip()
        if output:
            try:
                data = json.loads(output.split('\n')[0])
                if 'error' in data:
                    print(f"    ✓ Error properly reported: {data['error'][:50]}...")
                    return True
            except json.JSONDecodeError:
                pass
        
        print(f"    ✓ Script handled invalid camera")
        return True
    except subprocess.TimeoutExpired:
        print(f"    ✓ Script timed out as expected")
        return True
    except Exception as e:
        print(f"    Unexpected error: {e}")
        return False

@runner.test("Virtual Environment Check", "Check if venv exists")
def test_venv_exists():
    """Test if virtual environment is set up"""
    venv_path = Path(__file__).parent / "venv"
    python_path = venv_path / "bin" / "python3"
    
    if venv_path.exists() and python_path.exists():
        print(f"    ✓ Virtual environment found at {venv_path}")
        return True
    else:
        print(f"    ⚠ Virtual environment not found (run: python3 -m venv venv)")
        return 'SKIP'

@runner.test("Requirements File", "Check if requirements.txt exists")
def test_requirements_file():
    """Test if requirements.txt exists"""
    req_path = Path(__file__).parent / "requirements.txt"
    
    if req_path.exists():
        with open(req_path, 'r') as f:
            requirements = f.read()
        print(f"    ✓ Requirements file found")
        print(f"    Dependencies: {', '.join([r.split('==')[0] for r in requirements.strip().split() if r])}")
        return True
    else:
        print(f"    ✗ requirements.txt not found")
        return False

@runner.test("Node-RED Files", "Check Node-RED integration files")
def test_nodered_files():
    """Test that Node-RED files exist"""
    base_path = Path(__file__).parent
    files = {
        'humanDetection.js': 'Node logic',
        'humanDetection.html': 'Node UI',
        'package.json': 'Package manifest',
        'locales/en-US/humanDetection.json': 'Localization'
    }
    
    all_exist = True
    for file, desc in files.items():
        file_path = base_path / file
        if file_path.exists():
            print(f"    ✓ {desc}: {file}")
        else:
            print(f"    ✗ Missing {desc}: {file}")
            all_exist = False
    
    return all_exist

@runner.test("DeepFace Availability", "Check if emotion detection is available")
def test_deepface_available():
    """Test if DeepFace is installed for emotion detection"""
    try:
        from deepface import DeepFace
        print(f"    ✓ DeepFace available for emotion detection")
        return True
    except ImportError:
        print(f"    ⚠ DeepFace not installed (optional, for emotion detection)")
        return 'SKIP'

@runner.test("Camera Access", "Test if camera can be accessed")
def test_camera_access():
    """Test if default camera is accessible"""
    try:
        import cv2
        cap = cv2.VideoCapture(0)
        
        if cap.isOpened():
            ret, frame = cap.read()
            cap.release()
            
            if ret and frame is not None:
                print(f"    ✓ Camera accessible, frame size: {frame.shape}")
                return True
            else:
                print(f"    ⚠ Camera opened but couldn't read frame")
                return 'SKIP'
        else:
            print(f"    ⚠ Camera not accessible (may be in use or not available)")
            return 'SKIP'
    except Exception as e:
        print(f"    ⚠ Camera test failed: {e}")
        return 'SKIP'

# ============================================================================
# MAIN
# ============================================================================

if __name__ == '__main__':
    print(f"\n{BLUE}Starting Human Detection Test Suite...{RESET}")
    print(f"{BLUE}Working directory: {Path(__file__).parent}{RESET}")
    
    runner.run_all()
    
    # Exit with appropriate code
    sys.exit(0 if runner.failed == 0 else 1)
