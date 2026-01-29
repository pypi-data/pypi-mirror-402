import pytest

from ward.models import CodeFile
from ward.scanner import map_severity
from ward.server import CATEGORY_CONFIG_MAP
from ward.server import resolve_config
from ward.utilities.utils import detect_language
from ward.utilities.utils import LANGUAGE_EXTENSIONS


class TestDetectLanguage:
    def test_single_python_file(self):
        files = [CodeFile(path="app.py", content="x=1")]
        assert detect_language(files) == "python"

    def test_single_javascript_file(self):
        files = [CodeFile(path="index.js", content="x=1")]
        assert detect_language(files) == "javascript"

    def test_single_typescript_file(self):
        files = [CodeFile(path="app.ts", content="x=1")]
        assert detect_language(files) == "typescript"

    def test_single_tsx_file(self):
        files = [CodeFile(path="App.tsx", content="x=1")]
        assert detect_language(files) == "typescript"

    def test_single_go_file(self):
        files = [CodeFile(path="main.go", content="package main")]
        assert detect_language(files) == "go"

    def test_mixed_languages_returns_none(self):
        files = [
            CodeFile(path="a.py", content=""),
            CodeFile(path="b.js", content=""),
        ]
        assert detect_language(files) is None

    def test_unknown_extension_returns_none(self):
        files = [CodeFile(path="file.xyz", content="")]
        assert detect_language(files) is None

    def test_multiple_same_language(self):
        files = [
            CodeFile(path="a.py", content=""),
            CodeFile(path="b.py", content=""),
            CodeFile(path="c.py", content=""),
        ]
        assert detect_language(files) == "python"


class TestResolveConfig:
    def test_config_override_takes_precedence(self):
        assert resolve_config("all", "p/custom", []) == "p/custom"
        assert resolve_config("security", "p/override", []) == "p/override"

    def test_security_category(self):
        assert resolve_config("security", None, []) == "p/security-audit"

    def test_all_category(self):
        assert resolve_config("all", None, []) == "p/default"

    def test_bugs_category(self):
        assert resolve_config("bugs", None, []) == "p/default"

    def test_performance_category(self):
        assert resolve_config("performance", None, []) == "p/default"

    def test_quality_with_python_files(self):
        py_files = [CodeFile(path="app.py", content="x=1")]
        assert resolve_config("quality", None, py_files) == "p/python"

    def test_quality_with_javascript_files(self):
        js_files = [CodeFile(path="index.js", content="x=1")]
        assert resolve_config("quality", None, js_files) == "p/javascript"

    def test_quality_with_go_files(self):
        go_files = [CodeFile(path="main.go", content="package main")]
        assert resolve_config("quality", None, go_files) == "p/go"

    def test_quality_with_mixed_languages_fallback(self):
        mixed = [
            CodeFile(path="a.py", content=""),
            CodeFile(path="b.js", content=""),
        ]
        assert resolve_config("quality", None, mixed) == "p/default"

    def test_unknown_category_fallback(self):
        assert resolve_config("unknown", None, []) == "p/default"


class TestMapSeverity:
    def test_security_error_is_critical(self):
        metadata = {"category": "security"}
        assert map_severity("ERROR", metadata) == "critical"

    def test_security_warning_is_high(self):
        metadata = {"category": "security"}
        assert map_severity("WARNING", metadata) == "high"

    def test_cwe_indicator_treated_as_security(self):
        metadata = {"cwe": "CWE-89"}
        assert map_severity("ERROR", metadata) == "critical"

    def test_correctness_error_is_critical(self):
        metadata = {"category": "correctness"}
        assert map_severity("ERROR", metadata) == "critical"

    def test_bug_error_is_critical(self):
        metadata = {"category": "bug"}
        assert map_severity("ERROR", metadata) == "critical"

    def test_performance_error_is_high(self):
        metadata = {"category": "performance"}
        assert map_severity("ERROR", metadata) == "high"

    def test_performance_warning_is_medium(self):
        metadata = {"category": "performance"}
        assert map_severity("WARNING", metadata) == "medium"

    def test_default_error_is_high(self):
        metadata = {"category": "other"}
        assert map_severity("ERROR", metadata) == "high"

    def test_default_warning_is_medium(self):
        metadata = {}
        assert map_severity("WARNING", metadata) == "medium"

    def test_unknown_severity_is_low(self):
        metadata = {}
        assert map_severity("INFO", metadata) == "low"

    def test_case_insensitive_severity(self):
        metadata = {"category": "security"}
        assert map_severity("error", metadata) == "critical"
        assert map_severity("Error", metadata) == "critical"


class TestCategoryConfigMap:
    def test_all_categories_present(self):
        expected_categories = ["all", "security", "bugs", "performance"]
        for cat in expected_categories:
            assert cat in CATEGORY_CONFIG_MAP

    def test_config_values_are_valid(self):
        for config in CATEGORY_CONFIG_MAP.values():
            assert config.startswith("p/") or config == "auto"


class TestLanguageExtensions:
    def test_common_extensions_present(self):
        expected = [".py", ".js", ".ts", ".tsx", ".jsx", ".go", ".java"]
        for ext in expected:
            assert ext in LANGUAGE_EXTENSIONS

    def test_extensions_map_to_valid_languages(self):
        valid_languages = {
            "python", "javascript", "typescript", "go", "java",
            "ruby", "rust", "c", "cpp", "csharp", "php",
            "swift", "kotlin", "scala",
        }
        for lang in LANGUAGE_EXTENSIONS.values():
            assert lang in valid_languages
