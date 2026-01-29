"""Tests for Rope MCP Server refactoring tools."""

import json
import tempfile
from pathlib import Path

import pytest

from rope_mcp_server.offset import find_symbol_offset, list_top_level_symbols
from rope_mcp_server.refactoring import (
    convert_module_to_init,
    convert_module_to_package,
    extract_method,
    inline_variable,
    list_symbols,
    move_and_rename_module,
    move_module,
    move_symbol,
    rename_symbol,
)
from rope_mcp_server.rope_utils import close_all_projects


@pytest.fixture
def temp_project():
    """Create a temporary Python project."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)
        # Close projects BEFORE temp dir is deleted
        close_all_projects()


class TestOffset:
    """Tests for offset calculation."""

    def test_find_class_offset(self):
        content = "class Foo:\n    pass\n"
        offset = find_symbol_offset(content, "Foo", "class")
        assert content[offset : offset + 3] == "Foo"

    def test_find_function_offset(self):
        content = "def bar():\n    pass\n"
        offset = find_symbol_offset(content, "bar", "function")
        assert content[offset : offset + 3] == "bar"

    def test_find_async_function_offset(self):
        content = "async def baz():\n    pass\n"
        offset = find_symbol_offset(content, "baz", "function")
        assert content[offset : offset + 3] == "baz"

    def test_symbol_not_found(self):
        content = "class Foo:\n    pass\n"
        with pytest.raises(ValueError, match="not found"):
            find_symbol_offset(content, "Bar")

    def test_list_top_level_symbols(self):
        content = """
class MyClass:
    pass

def my_function():
    pass

MY_VAR = 42
"""
        symbols = list_top_level_symbols(content)
        names = [s.name for s in symbols]
        assert "MyClass" in names
        assert "my_function" in names
        assert "MY_VAR" in names


class TestListSymbols:
    """Tests for list_symbols tool."""

    def test_list_symbols_basic(self, temp_project):
        source = temp_project / "source.py"
        source.write_text(
            """
class Foo:
    pass

def bar():
    pass

CONSTANT = 123
"""
        )

        result = json.loads(list_symbols(str(temp_project), "source.py"))
        assert result["success"] is True
        names = [s["name"] for s in result["symbols"]]
        assert "Foo" in names
        assert "bar" in names
        assert "CONSTANT" in names

    def test_list_symbols_file_not_found(self, temp_project):
        result = json.loads(list_symbols(str(temp_project), "nonexistent.py"))
        assert result["success"] is False
        assert "error" in result


class TestMoveSymbol:
    """Tests for move_symbol tool."""

    def test_move_class(self, temp_project):
        source = temp_project / "source.py"
        source.write_text(
            """class Foo:
    pass


def bar():
    return Foo()
"""
        )

        result = json.loads(
            move_symbol(str(temp_project), "source.py", "Foo", "models.py")
        )
        assert result["success"] is True
        assert "models.py" in result["changed_files"]

        # Check that class was moved
        dest = temp_project / "models.py"
        assert dest.exists()
        assert "class Foo" in dest.read_text()

        # Check that import was updated in source using 'from-global' style
        source_content = source.read_text()
        assert "class Foo" not in source_content
        assert "from models import Foo" in source_content

    def test_move_function(self, temp_project):
        source = temp_project / "source.py"
        source.write_text(
            """def helper():
    return 42


def main():
    return helper()
"""
        )

        result = json.loads(
            move_symbol(str(temp_project), "source.py", "helper", "utils.py")
        )
        assert result["success"] is True

        # Check that function was moved
        dest = temp_project / "utils.py"
        assert dest.exists()
        assert "def helper" in dest.read_text()

    def test_move_symbol_not_found(self, temp_project):
        source = temp_project / "source.py"
        source.write_text("class Foo:\n    pass\n")

        result = json.loads(
            move_symbol(str(temp_project), "source.py", "NonExistent", "dest.py")
        )
        assert result["success"] is False
        assert "not found" in result["error"]


class TestRenameSymbol:
    """Tests for rename_symbol tool."""

    def test_rename_class(self, temp_project):
        source = temp_project / "source.py"
        source.write_text(
            """class OldName:
    pass


instance = OldName()
"""
        )

        result = json.loads(
            rename_symbol(str(temp_project), "source.py", "OldName", "NewName")
        )
        assert result["success"] is True

        content = source.read_text()
        assert "class NewName" in content
        assert "instance = NewName()" in content
        assert "OldName" not in content

    def test_rename_function(self, temp_project):
        source = temp_project / "source.py"
        source.write_text(
            """def old_func():
    pass


old_func()
"""
        )

        result = json.loads(
            rename_symbol(str(temp_project), "source.py", "old_func", "new_func")
        )
        assert result["success"] is True

        content = source.read_text()
        assert "def new_func" in content
        assert "new_func()" in content
        assert "old_func" not in content

    def test_rename_across_files(self, temp_project):
        module_a = temp_project / "module_a.py"
        module_a.write_text(
            """class SharedClass:
    pass
"""
        )

        module_b = temp_project / "module_b.py"
        module_b.write_text(
            """from module_a import SharedClass

instance = SharedClass()
"""
        )

        result = json.loads(
            rename_symbol(str(temp_project), "module_a.py", "SharedClass", "RenamedClass")
        )
        assert result["success"] is True

        # Both files should be changed
        assert "module_a.py" in result["changed_files"]
        assert "module_b.py" in result["changed_files"]

        # Verify content
        assert "class RenamedClass" in module_a.read_text()
        assert "from module_a import RenamedClass" in module_b.read_text()
        assert "instance = RenamedClass()" in module_b.read_text()


class TestExtractMethod:
    """Tests for extract_method tool."""

    def test_extract_simple_code(self, temp_project):
        source = temp_project / "source.py"
        source.write_text(
            """def main():
    x = 1
    y = 2
    result = x + y
    return result
"""
        )

        # Extract "result = x + y" (line 4)
        result = json.loads(
            extract_method(
                str(temp_project),
                "source.py",
                start_line=4,
                start_col=4,
                end_line=4,
                end_col=18,
                new_name="compute_sum",
            )
        )
        assert result["success"] is True

        content = source.read_text()
        assert "def compute_sum" in content


class TestInlineVariable:
    """Tests for inline_variable tool."""

    def test_inline_simple_variable(self, temp_project):
        source = temp_project / "source.py"
        source.write_text(
            """def main():
    temp = 42
    return temp + temp
"""
        )

        result = json.loads(
            inline_variable(str(temp_project), "source.py", "temp", line=2)
        )
        assert result["success"] is True

        content = source.read_text()
        assert "temp = 42" not in content
        assert "return 42 + 42" in content


class TestMoveModule:
    """Tests for move_module tool."""

    def test_move_module_to_folder(self, temp_project):
        # Create source module
        source = temp_project / "utils.py"
        source.write_text(
            """def helper():
    return 42
"""
        )

        # Create destination folder
        dest_folder = temp_project / "lib"
        dest_folder.mkdir()
        (dest_folder / "__init__.py").write_text("")

        # Create a file that imports from utils
        main = temp_project / "main.py"
        main.write_text(
            """from utils import helper

result = helper()
"""
        )

        result = json.loads(
            move_module(str(temp_project), "utils.py", "lib")
        )
        assert result["success"] is True

        # Check module was moved
        assert not source.exists()
        assert (dest_folder / "utils.py").exists()
        assert "def helper" in (dest_folder / "utils.py").read_text()

        # Check import was updated
        main_content = main.read_text()
        assert "from lib.utils import helper" in main_content

    def test_move_package_to_folder(self, temp_project):
        # Create source package
        pkg = temp_project / "mypackage"
        pkg.mkdir()
        (pkg / "__init__.py").write_text("from .core import MyClass\n")
        (pkg / "core.py").write_text(
            """class MyClass:
    pass
"""
        )

        # Create destination folder
        dest_folder = temp_project / "lib"
        dest_folder.mkdir()
        (dest_folder / "__init__.py").write_text("")

        # Create a file that imports from the package
        main = temp_project / "main.py"
        main.write_text(
            """from mypackage import MyClass

obj = MyClass()
"""
        )

        result = json.loads(
            move_module(str(temp_project), "mypackage", "lib")
        )
        assert result["success"] is True

        # Check package was moved
        assert not pkg.exists()
        assert (dest_folder / "mypackage").exists()
        assert (dest_folder / "mypackage" / "__init__.py").exists()
        assert (dest_folder / "mypackage" / "core.py").exists()

        # Check import was updated
        main_content = main.read_text()
        assert "from lib.mypackage import MyClass" in main_content


class TestConvertModuleToPackage:
    """Tests for convert_module_to_package tool."""

    def test_convert_simple_module(self, temp_project):
        # Create module
        (temp_project / "utils.py").write_text(
            """def helper():
    return 42
"""
        )

        # Create file that imports from module
        (temp_project / "main.py").write_text(
            """from utils import helper

result = helper()
"""
        )

        result = json.loads(
            convert_module_to_package(str(temp_project), "utils.py")
        )
        assert result["success"] is True
        assert result["new_module_path"] == "utils/utils.py"

        # Check structure
        assert not (temp_project / "utils.py").exists()
        assert (temp_project / "utils").is_dir()
        assert (temp_project / "utils" / "__init__.py").exists()
        assert (temp_project / "utils" / "utils.py").exists()
        assert "def helper" in (temp_project / "utils" / "utils.py").read_text()

        # Check import was updated
        main_content = (temp_project / "main.py").read_text()
        assert "from utils.utils import helper" in main_content

    def test_convert_nested_module(self, temp_project):
        # Create Django-like structure
        views = temp_project / "app" / "views"
        views.mkdir(parents=True)
        (temp_project / "app" / "__init__.py").write_text("")
        (views / "__init__.py").write_text("")
        (views / "service_contractor.py").write_text(
            """class ServiceContractorListView:
    pass

class ServiceContractorDetailView:
    pass
"""
        )

        # Create URL file that imports
        (temp_project / "app" / "urls.py").write_text(
            """from app.views.service_contractor import ServiceContractorListView, ServiceContractorDetailView

urlpatterns = []
"""
        )

        result = json.loads(
            convert_module_to_package(str(temp_project), "app/views/service_contractor.py")
        )
        assert result["success"] is True
        assert result["new_module_path"] == "app/views/service_contractor/service_contractor.py"

        # Check structure
        assert not (views / "service_contractor.py").exists()
        assert (views / "service_contractor").is_dir()
        assert (views / "service_contractor" / "__init__.py").exists()
        assert (views / "service_contractor" / "service_contractor.py").exists()

        # Check import was updated
        urls_content = (temp_project / "app" / "urls.py").read_text()
        assert "from app.views.service_contractor.service_contractor import" in urls_content
        assert "ServiceContractorListView" in urls_content
        assert "ServiceContractorDetailView" in urls_content

    def test_convert_module_not_py_file(self, temp_project):
        (temp_project / "folder").mkdir()

        result = json.loads(
            convert_module_to_package(str(temp_project), "folder")
        )
        assert result["success"] is False
        assert "must be a .py file" in result["error"]

    def test_convert_module_target_dir_exists(self, temp_project):
        # Create module
        (temp_project / "utils.py").write_text("def helper(): pass\n")

        # Create directory with same name (e.g. from failed previous attempt)
        (temp_project / "utils").mkdir()

        result = json.loads(
            convert_module_to_package(str(temp_project), "utils.py")
        )
        assert result["success"] is False
        assert "already exists" in result["error"]

    def test_convert_module_warns_about_string_refs(self, temp_project):
        # Create module
        (temp_project / "mymodule.py").write_text(
            """class MyClass:
    pass
"""
        )

        # Create test file with mock.patch string reference
        (temp_project / "test_mymodule.py").write_text(
            """from unittest import mock

@mock.patch("mymodule.MyClass")
def test_something():
    pass
"""
        )

        result = json.loads(
            convert_module_to_package(str(temp_project), "mymodule.py")
        )
        assert result["success"] is True

        # Should warn about the string reference in mock.patch
        assert "warning_string_references" in result
        assert len(result["warning_string_references"]) > 0
        assert any("test_mymodule.py" in ref for ref in result["warning_string_references"])


class TestConvertModuleToInit:
    """Tests for convert_module_to_init tool."""

    def test_convert_simple_module(self, temp_project):
        # Create module
        (temp_project / "utils.py").write_text(
            """def helper():
    return 42

class MyClass:
    pass
"""
        )

        # Create file that imports from module
        (temp_project / "main.py").write_text(
            """from utils import helper, MyClass

result = helper()
"""
        )

        result = json.loads(
            convert_module_to_init(str(temp_project), "utils.py")
        )
        assert result["success"] is True
        assert result["new_path"] == "utils/__init__.py"
        assert result["package_dir"] == "utils"

        # Check structure
        assert not (temp_project / "utils.py").exists()
        assert (temp_project / "utils").is_dir()
        assert (temp_project / "utils" / "__init__.py").exists()
        assert "def helper" in (temp_project / "utils" / "__init__.py").read_text()

        # Import should still work (unchanged!)
        main_content = (temp_project / "main.py").read_text()
        assert "from utils import helper, MyClass" in main_content

    def test_convert_nested_module(self, temp_project):
        # Create Django-like structure
        views = temp_project / "app" / "views"
        views.mkdir(parents=True)
        (temp_project / "app" / "__init__.py").write_text("")
        (views / "__init__.py").write_text("")
        (views / "customer_order.py").write_text(
            """class CustomerOrderListView:
    pass

class CustomerOrderDetailView:
    pass
"""
        )

        # Create URL file that imports
        (temp_project / "app" / "urls.py").write_text(
            """from app.views.customer_order import CustomerOrderListView

urlpatterns = []
"""
        )

        result = json.loads(
            convert_module_to_init(str(temp_project), "app/views/customer_order.py")
        )
        assert result["success"] is True
        assert result["new_path"] == "app/views/customer_order/__init__.py"

        # Check structure
        assert not (views / "customer_order.py").exists()
        assert (views / "customer_order").is_dir()
        assert (views / "customer_order" / "__init__.py").exists()

        # Import should still work (unchanged!)
        urls_content = (temp_project / "app" / "urls.py").read_text()
        assert "from app.views.customer_order import CustomerOrderListView" in urls_content

    def test_convert_module_target_dir_exists(self, temp_project):
        (temp_project / "utils.py").write_text("def helper(): pass\n")
        (temp_project / "utils").mkdir()

        result = json.loads(
            convert_module_to_init(str(temp_project), "utils.py")
        )
        assert result["success"] is False
        assert "already exists" in result["error"]

    def test_convert_module_not_found(self, temp_project):
        result = json.loads(
            convert_module_to_init(str(temp_project), "nonexistent.py")
        )
        assert result["success"] is False
        assert "does not exist" in result["error"]


class TestMoveAndRenameModule:
    """Tests for move_and_rename_module tool."""

    def test_move_and_explicit_rename(self, temp_project):
        # Create Django-like structure
        views = temp_project / "app" / "views"
        views.mkdir(parents=True)
        (temp_project / "app" / "__init__.py").write_text("")
        (views / "__init__.py").write_text("")
        (views / "service_contractor_extra.py").write_text(
            """class ServiceContractorExtraView:
    pass
"""
        )

        # Create package to move into
        sc_pkg = views / "service_contractor"
        sc_pkg.mkdir()
        (sc_pkg / "__init__.py").write_text("")

        # Create URL file that imports
        (temp_project / "app" / "urls.py").write_text(
            """from app.views.service_contractor_extra import ServiceContractorExtraView

urlpatterns = []
"""
        )

        result = json.loads(
            move_and_rename_module(
                str(temp_project),
                "app/views/service_contractor_extra.py",
                "app/views/service_contractor",
                new_name="extra"
            )
        )
        assert result["success"] is True

        # Check old file gone
        assert not (views / "service_contractor_extra.py").exists()

        # Check new file exists
        assert (sc_pkg / "extra.py").exists()
        assert "class ServiceContractorExtraView" in (sc_pkg / "extra.py").read_text()

        # Check import was updated
        urls_content = (temp_project / "app" / "urls.py").read_text()
        assert "from app.views.service_contractor.extra import ServiceContractorExtraView" in urls_content

    def test_move_and_autodetect_rename(self, temp_project):
        # Create structure
        views = temp_project / "views"
        views.mkdir()
        (views / "__init__.py").write_text("")
        (views / "customer_order_mixins.py").write_text(
            """class CustomerOrderMixin:
    pass
"""
        )

        # Create package with matching name
        co_pkg = views / "customer_order"
        co_pkg.mkdir()
        (co_pkg / "__init__.py").write_text("")

        # Create file that imports
        (temp_project / "main.py").write_text(
            """from views.customer_order_mixins import CustomerOrderMixin

obj = CustomerOrderMixin()
"""
        )

        # Auto-detect: customer_order_mixins → customer_order/mixins
        result = json.loads(
            move_and_rename_module(
                str(temp_project),
                "views/customer_order_mixins.py",
                "views/customer_order"
                # new_name=None triggers auto-detect
            )
        )
        assert result["success"] is True

        # Check file was moved and renamed
        assert not (views / "customer_order_mixins.py").exists()
        assert (co_pkg / "mixins.py").exists()

        # Check import updated
        main_content = (temp_project / "main.py").read_text()
        assert "from views.customer_order.mixins import CustomerOrderMixin" in main_content

    def test_move_without_rename_no_prefix(self, temp_project):
        # When module name doesn't start with dest folder name, just move
        lib = temp_project / "lib"
        lib.mkdir()
        (lib / "__init__.py").write_text("")

        (temp_project / "helpers.py").write_text(
            """def help_func():
    return 42
"""
        )

        (temp_project / "main.py").write_text(
            """from helpers import help_func

result = help_func()
"""
        )

        result = json.loads(
            move_and_rename_module(
                str(temp_project),
                "helpers.py",
                "lib"
                # new_name=None, but "helpers" doesn't start with "lib_"
            )
        )
        assert result["success"] is True

        # Should just move without rename
        assert not (temp_project / "helpers.py").exists()
        assert (lib / "helpers.py").exists()

        # Import updated
        main_content = (temp_project / "main.py").read_text()
        assert "from lib.helpers import help_func" in main_content

    def test_move_and_rename_not_py_file(self, temp_project):
        (temp_project / "folder").mkdir()

        result = json.loads(
            move_and_rename_module(str(temp_project), "folder", "dest")
        )
        assert result["success"] is False
        assert "must be a .py file" in result["error"]

    def test_move_with_conflicting_imports_workaround(self, temp_project):
        """Test workaround for Rope bug with conflicting imports.

        Rope crashes when a file has imports from BOTH:
        1. The destination package (e.g., from views.service_contractor import X)
        2. The module being moved (e.g., from views.service_contractor_extra import Y)

        The workaround temporarily hides such files during the move.
        """
        views = temp_project / "views"
        views.mkdir()
        (views / "__init__.py").write_text("")

        # Create destination package
        sc_pkg = views / "service_contractor"
        sc_pkg.mkdir()
        (sc_pkg / "__init__.py").write_text(
            """class ServiceContractorListView:
    pass
"""
        )

        # Create module to be moved
        (views / "service_contractor_extra.py").write_text(
            """class ServiceContractorExtraView:
    pass
"""
        )

        # Create file with CONFLICTING imports (both dest package AND module being moved)
        # This would cause Rope to crash without the workaround
        (temp_project / "urls.py").write_text(
            """from views.service_contractor import ServiceContractorListView
from views.service_contractor_extra import ServiceContractorExtraView

urlpatterns = [ServiceContractorListView, ServiceContractorExtraView]
"""
        )

        result = json.loads(
            move_and_rename_module(
                str(temp_project),
                "views/service_contractor_extra.py",
                "views/service_contractor",
                new_name="extra"
            )
        )

        # Should succeed (workaround should handle it)
        assert result["success"] is True, f"Failed: {result.get('error')}"

        # Module should be moved and renamed
        assert not (views / "service_contractor_extra.py").exists()
        assert (sc_pkg / "extra.py").exists()

        # The conflicting file should have been fixed manually
        urls_content = (temp_project / "urls.py").read_text()
        assert "from views.service_contractor.extra import ServiceContractorExtraView" in urls_content
        # Original import should still be there
        assert "from views.service_contractor import ServiceContractorListView" in urls_content

        # Result should indicate files were manually fixed
        if "manually_fixed_files" in result:
            assert "urls.py" in result["manually_fixed_files"]

    def test_move_with_conflicting_relative_imports(self, temp_project):
        """Test that relative imports are also fixed in conflicting files.

        Example: __init__.py has `from .service_contractor_extra import X`
        which needs to become `from .extra import X`
        """
        views = temp_project / "views"
        views.mkdir()
        (views / "__init__.py").write_text("")

        # Create destination package with __init__.py that has BOTH imports
        sc_pkg = views / "service_contractor"
        sc_pkg.mkdir()
        # This __init__.py imports from itself AND from the module we're moving (relative import)
        (sc_pkg / "__init__.py").write_text(
            """from .base import ServiceContractorBase
from .service_contractor_extra import ServiceContractorExtraView
"""
        )
        (sc_pkg / "base.py").write_text(
            """class ServiceContractorBase:
    pass
"""
        )

        # Create module to be moved (currently outside the package, will move inside)
        (views / "service_contractor_extra.py").write_text(
            """class ServiceContractorExtraView:
    pass
"""
        )

        # Also create a file with absolute imports for completeness
        (temp_project / "urls.py").write_text(
            """from views.service_contractor import ServiceContractorBase
from views.service_contractor_extra import ServiceContractorExtraView

urlpatterns = []
"""
        )

        result = json.loads(
            move_and_rename_module(
                str(temp_project),
                "views/service_contractor_extra.py",
                "views/service_contractor",
                new_name="extra"
            )
        )

        assert result["success"] is True, f"Failed: {result.get('error')}"

        # Module should be moved and renamed
        assert not (views / "service_contractor_extra.py").exists()
        assert (sc_pkg / "extra.py").exists()

        # Check that __init__.py relative import was fixed
        init_content = (sc_pkg / "__init__.py").read_text()
        assert "from .extra import ServiceContractorExtraView" in init_content
        assert "from .base import ServiceContractorBase" in init_content  # unchanged

        # Check that urls.py absolute import was also fixed
        urls_content = (temp_project / "urls.py").read_text()
        assert "from views.service_contractor.extra import ServiceContractorExtraView" in urls_content
