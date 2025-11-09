"""
Test cases cho module utils_markdownTable_to_xlsx.py

Test các edge cases:
1. Bảng có số cột không đều giữa các dòng
2. Ô chứa ký tự pipe (|) trong nội dung
3. Header trống hoặc không có header
4. Bảng có nhiều dòng separator liên tiếp
5. Ô có khoảng trắng thừa hoặc ký tự đặc biệt
6. Bảng không có separator line
7. Bảng rỗng hoặc không hợp lệ
8. Bảng có ô trống
"""

import unittest
import tempfile
import os
from pathlib import Path

# Import functions to test
from utils_markdownTable_to_xlsx import (
    _is_separator_line,
    _parse_markdown_table,
    _create_dataframe_from_rows,
    markdownTable_to_xlsx
)

try:
    import pandas as pd
    PANDAS_AVAILABLE = True
except ImportError:
    PANDAS_AVAILABLE = False


class TestSeparatorLine(unittest.TestCase):
    """Test hàm _is_separator_line"""
    
    def test_standard_separator(self):
        """Test separator chuẩn"""
        self.assertTrue(_is_separator_line("| --- | --- | --- |"))
        self.assertTrue(_is_separator_line("|---|----|---|"))
    
    def test_separator_with_alignment(self):
        """Test separator với căn chỉnh"""
        self.assertTrue(_is_separator_line("| :--- | :---: | ---: |"))
        self.assertTrue(_is_separator_line("|:---|:---:|---:|"))
    
    def test_not_separator(self):
        """Test các dòng không phải separator"""
        self.assertFalse(_is_separator_line("| Mã số | CHỈ TIÊU |"))
        self.assertFalse(_is_separator_line("| 01 | Doanh thu |"))
        self.assertFalse(_is_separator_line("---"))
        self.assertFalse(_is_separator_line(""))


class TestParseMarkdownTable(unittest.TestCase):
    """Test hàm _parse_markdown_table"""
    
    def test_standard_table(self):
        """Test bảng chuẩn"""
        table = """| Col1 | Col2 |
| --- | --- |
| A | B |
| C | D |"""
        rows = _parse_markdown_table(table)
        self.assertEqual(len(rows), 3)  # Header + 2 data rows
        self.assertEqual(rows[0], ['Col1', 'Col2'])
        self.assertEqual(rows[1], ['A', 'B'])
        self.assertEqual(rows[2], ['C', 'D'])
    
    def test_table_without_separator(self):
        """Test bảng không có separator line"""
        table = """| Col1 | Col2 |
| A | B |"""
        rows = _parse_markdown_table(table)
        self.assertEqual(len(rows), 2)
        self.assertEqual(rows[0], ['Col1', 'Col2'])
        self.assertEqual(rows[1], ['A', 'B'])
    
    def test_table_with_multiple_separators(self):
        """Test bảng có nhiều separator liên tiếp"""
        table = """| Col1 | Col2 |
| --- | --- |
| --- | --- |
| A | B |"""
        rows = _parse_markdown_table(table)
        self.assertEqual(len(rows), 2)  # Header + 1 data row (separators bị skip)
        self.assertEqual(rows[0], ['Col1', 'Col2'])
        self.assertEqual(rows[1], ['A', 'B'])
    
    def test_table_with_empty_lines(self):
        """Test bảng có dòng trống"""
        table = """| Col1 | Col2 |

| --- | --- |

| A | B |

| C | D |"""
        rows = _parse_markdown_table(table)
        self.assertEqual(len(rows), 3)  # Header + 2 data rows
        self.assertEqual(rows[0], ['Col1', 'Col2'])
        self.assertEqual(rows[1], ['A', 'B'])
        self.assertEqual(rows[2], ['C', 'D'])
    
    def test_table_with_uneven_columns(self):
        """Test bảng có số cột không đều - EDGE CASE 1"""
        table = """| Col1 | Col2 |
| --- | --- |
| A | B | C |
| D |"""
        rows = _parse_markdown_table(table)
        # Should still parse, but columns will be uneven
        self.assertEqual(len(rows), 3)
        self.assertEqual(rows[0], ['Col1', 'Col2'])
        self.assertEqual(rows[1], ['A', 'B', 'C'])  # Thừa cột
        self.assertEqual(rows[2], ['D'])  # Thiếu cột
    
    def test_table_with_pipe_in_content(self):
        """Test bảng có pipe trong nội dung - EDGE CASE 2"""
        # Note: Markdown standard doesn't support pipes in content easily
        # But we should handle it gracefully
        table = """| Name | Description |
| --- | --- |
| Test | Value with | pipe |"""
        rows = _parse_markdown_table(table)
        # Current implementation will split on pipe, so this will create extra columns
        # This is expected behavior for now
        self.assertEqual(len(rows), 2)
        # The pipe in content will be split
        self.assertTrue(len(rows[1]) >= 2)
    
    def test_table_with_empty_cells(self):
        """Test bảng có ô trống"""
        table = """| Col1 | Col2 | Col3 |
| --- | --- | --- |
| A |  | C |
|  | B |  |"""
        rows = _parse_markdown_table(table)
        self.assertEqual(len(rows), 3)
        self.assertEqual(rows[0], ['Col1', 'Col2', 'Col3'])
        self.assertEqual(rows[1], ['A', '', 'C'])
        self.assertEqual(rows[2], ['', 'B', ''])
    
    def test_table_with_whitespace(self):
        """Test bảng có khoảng trắng thừa"""
        table = """|  Col1  |  Col2  |
|  ---  |  ---  |
|  A  |  B  |"""
        rows = _parse_markdown_table(table)
        self.assertEqual(len(rows), 2)
        self.assertEqual(rows[0], ['Col1', 'Col2'])  # Whitespace should be stripped
        self.assertEqual(rows[1], ['A', 'B'])
    
    def test_empty_table(self):
        """Test bảng rỗng"""
        table = ""
        rows = _parse_markdown_table(table)
        self.assertEqual(len(rows), 0)
    
    def test_table_with_only_separator(self):
        """Test bảng chỉ có separator"""
        table = "| --- | --- |"
        rows = _parse_markdown_table(table)
        self.assertEqual(len(rows), 0)  # Separator bị skip


class TestCreateDataFrame(unittest.TestCase):
    """Test hàm _create_dataframe_from_rows"""
    
    @unittest.skipUnless(PANDAS_AVAILABLE, "pandas not available")
    def test_standard_dataframe(self):
        """Test tạo DataFrame chuẩn"""
        rows = [
            ['Col1', 'Col2'],
            ['A', 'B'],
            ['C', 'D']
        ]
        df = _create_dataframe_from_rows(rows)
        self.assertEqual(len(df), 2)
        self.assertEqual(list(df.columns), ['Col1', 'Col2'])
        self.assertEqual(df.iloc[0]['Col1'], 'A')
        self.assertEqual(df.iloc[0]['Col2'], 'B')
    
    @unittest.skipUnless(PANDAS_AVAILABLE, "pandas not available")
    def test_dataframe_with_uneven_columns(self):
        """Test DataFrame với số cột không đều - EDGE CASE 1"""
        rows = [
            ['Col1', 'Col2'],
            ['A', 'B', 'C'],  # Thừa cột
            ['D']  # Thiếu cột
        ]
        # Should handle gracefully by padding/truncating
        df = _create_dataframe_from_rows(rows)
        self.assertEqual(len(df), 2)
        self.assertEqual(list(df.columns), ['Col1', 'Col2'])
        # Row with extra column should be truncated
        self.assertEqual(df.iloc[0]['Col1'], 'A')
        self.assertEqual(df.iloc[0]['Col2'], 'B')
        # Row with missing column should have NaN or empty
        self.assertEqual(df.iloc[1]['Col1'], 'D')
        # Check if Col2 is NaN or empty string
        self.assertTrue(pd.isna(df.iloc[1]['Col2']) or df.iloc[1]['Col2'] == '')
    
    @unittest.skipUnless(PANDAS_AVAILABLE, "pandas not available")
    def test_dataframe_with_empty_header(self):
        """Test DataFrame với header trống - EDGE CASE 3"""
        rows = [
            ['', 'Col2'],
            ['A', 'B']
        ]
        df = _create_dataframe_from_rows(rows)
        self.assertEqual(len(df), 1)
        # Empty header should be handled (pandas will create a column name)
        self.assertEqual(len(df.columns), 2)
    
    @unittest.skipUnless(PANDAS_AVAILABLE, "pandas not available")
    def test_dataframe_with_only_header(self):
        """Test DataFrame chỉ có header"""
        rows = [['Col1', 'Col2']]
        df = _create_dataframe_from_rows(rows)
        self.assertEqual(len(df), 0)  # No data rows
        self.assertEqual(list(df.columns), ['Col1', 'Col2'])
    
    @unittest.skipUnless(PANDAS_AVAILABLE, "pandas not available")
    def test_empty_rows(self):
        """Test với rows rỗng"""
        with self.assertRaises(ValueError):
            _create_dataframe_from_rows([])


class TestMarkdownTableToXlsx(unittest.TestCase):
    """Test hàm markdownTable_to_xlsx"""
    
    @unittest.skipUnless(PANDAS_AVAILABLE, "pandas not available")
    def test_standard_conversion(self):
        """Test chuyển đổi chuẩn"""
        table = """| Col1 | Col2 |
| --- | --- |
| A | B |
| C | D |"""
        
        with tempfile.NamedTemporaryFile(suffix='.xlsx', delete=False) as tmp:
            output_path = tmp.name
        
        try:
            result_path = markdownTable_to_xlsx(table, output_path)
            self.assertEqual(result_path, output_path)
            self.assertTrue(os.path.exists(result_path))
            
            # Verify Excel file can be read
            df = pd.read_excel(result_path, engine='openpyxl')
            self.assertEqual(len(df), 2)
            self.assertEqual(list(df.columns), ['Col1', 'Col2'])
        finally:
            if os.path.exists(output_path):
                os.remove(output_path)
    
    @unittest.skipUnless(PANDAS_AVAILABLE, "pandas not available")
    def test_conversion_with_uneven_columns(self):
        """Test chuyển đổi với số cột không đều - EDGE CASE 1"""
        table = """| Col1 | Col2 |
| --- | --- |
| A | B | C |
| D |"""
        
        with tempfile.NamedTemporaryFile(suffix='.xlsx', delete=False) as tmp:
            output_path = tmp.name
        
        try:
            # Should not raise error, but handle gracefully
            result_path = markdownTable_to_xlsx(table, output_path)
            self.assertTrue(os.path.exists(result_path))
            
            # Verify Excel file can be read
            df = pd.read_excel(result_path, engine='openpyxl')
            self.assertEqual(len(df), 2)
            self.assertEqual(list(df.columns), ['Col1', 'Col2'])
        finally:
            if os.path.exists(output_path):
                os.remove(output_path)
    
    @unittest.skipUnless(PANDAS_AVAILABLE, "pandas not available")
    def test_conversion_with_empty_cells(self):
        """Test chuyển đổi với ô trống"""
        table = """| Col1 | Col2 | Col3 |
| --- | --- | --- |
| A |  | C |
|  | B |  |"""
        
        with tempfile.NamedTemporaryFile(suffix='.xlsx', delete=False) as tmp:
            output_path = tmp.name
        
        try:
            result_path = markdownTable_to_xlsx(table, output_path)
            self.assertTrue(os.path.exists(result_path))
            
            df = pd.read_excel(result_path, engine='openpyxl')
            self.assertEqual(len(df), 2)
            self.assertEqual(list(df.columns), ['Col1', 'Col2', 'Col3'])
        finally:
            if os.path.exists(output_path):
                os.remove(output_path)
    
    @unittest.skipUnless(PANDAS_AVAILABLE, "pandas not available")
    def test_empty_table_error(self):
        """Test lỗi khi bảng rỗng"""
        table = ""
        with tempfile.NamedTemporaryFile(suffix='.xlsx', delete=False) as tmp:
            output_path = tmp.name
        
        try:
            with self.assertRaises(ValueError):
                markdownTable_to_xlsx(table, output_path)
        finally:
            if os.path.exists(output_path):
                os.remove(output_path)
    
    @unittest.skipUnless(PANDAS_AVAILABLE, "pandas not available")
    def test_auto_output_path(self):
        """Test tự động tạo output path"""
        table = """| Col1 | Col2 |
| --- | --- |
| A | B |"""
        
        result_path = markdownTable_to_xlsx(table)
        self.assertTrue(os.path.exists(result_path))
        self.assertTrue(result_path.endswith('.xlsx'))
        
        # Cleanup
        if os.path.exists(result_path):
            os.remove(result_path)


if __name__ == '__main__':
    unittest.main()


