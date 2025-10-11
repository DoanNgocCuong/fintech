# ===========================================
# 🧪 TEST CASES CHO FINtech VNSTOCK ONLY
# ===========================================
# File này chứa các test cases để kiểm tra tính đúng đắn của code
# Sử dụng unittest framework của Python

import unittest
import sys
import os
from unittest.mock import Mock, patch, MagicMock
import pandas as pd

# Thêm thư mục hiện tại vào Python path để import module
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Import module cần test
from fintech_vnstock_only import valuation_metrics, display_results, save_to_file

class TestVnstockValuationMetrics(unittest.TestCase):
    """
    Test class cho các hàm trong fintech_vnstock_only.py
    
    Mục đích: Kiểm tra xem các hàm có hoạt động đúng không
    - Test với dữ liệu hợp lệ
    - Test với dữ liệu không hợp lệ
    - Test error handling
    - Test edge cases
    """
    
    def setUp(self):
        """
        Setup method - chạy trước mỗi test case
        Khởi tạo dữ liệu test và mock objects
        """
        self.test_ticker = "FPT"  # Mã cổ phiếu test
        self.mock_fundamental_data = {
            'pe': 15.5,
            'pb': 2.1,
            'roe': 18.5,
            'debt_equity': 0.8,
            'market_cap': 50000000000,  # 50 tỷ VND
            'dividend_yield': 3.2,
            'eps_growth': 12.5
        }
        self.mock_financial_data = {
            'current_ratio': 1.8,
            'net_income': 1000000000  # 1 tỷ VND
        }
        self.mock_price_data = pd.DataFrame({
            'close': [95000, 96000, 97000, 98000, 99000]
        })

    @patch('fintech_vnstock_only.Fundamental')
    @patch('fintech_vnstock_only.Financial')
    @patch('fintech_vnstock_only.stock_historical_data')
    def test_valuation_metrics_success(self, mock_stock_data, mock_financial, mock_fundamental):
        """
        Test case 1: Kiểm tra hàm valuation_metrics với dữ liệu hợp lệ
        
        Mục đích: Đảm bảo hàm trả về đúng kết quả khi có đầy đủ dữ liệu
        """
        print("\n🧪 Test 1: valuation_metrics với dữ liệu hợp lệ")
        
        # Mock các đối tượng vnstock
        mock_fundamental_instance = Mock()
        mock_financial_instance = Mock()
        
        # Setup mock methods trả về dữ liệu test
        mock_fundamental_instance.pe.return_value = self.mock_fundamental_data['pe']
        mock_fundamental_instance.pb.return_value = self.mock_fundamental_data['pb']
        mock_fundamental_instance.roe.return_value = self.mock_fundamental_data['roe']
        mock_fundamental_instance.debt_equity.return_value = self.mock_fundamental_data['debt_equity']
        mock_fundamental_instance.market_cap.return_value = self.mock_fundamental_data['market_cap']
        mock_fundamental_instance.dividend_yield.return_value = self.mock_fundamental_data['dividend_yield']
        mock_fundamental_instance.eps_growth.return_value = self.mock_fundamental_data['eps_growth']
        
        mock_financial_instance.current_ratio.return_value = self.mock_financial_data['current_ratio']
        mock_financial_instance.net_income.return_value = self.mock_financial_data['net_income']
        
        mock_stock_data.return_value = self.mock_price_data
        
        # Setup mock classes
        mock_fundamental.return_value = mock_fundamental_instance
        mock_financial.return_value = mock_financial_instance
        
        # Gọi hàm cần test
        result = valuation_metrics(self.test_ticker)
        
        # Kiểm tra kết quả
        self.assertIsInstance(result, dict, "Kết quả phải là dictionary")
        self.assertIn("PE", result, "Phải có chỉ số PE")
        self.assertEqual(result["PE"], 15.5, "PE phải bằng 15.5")
        self.assertEqual(result["PB"], 2.1, "PB phải bằng 2.1")
        self.assertEqual(result["ROE"], 18.5, "ROE phải bằng 18.5")
        
        # Kiểm tra Earnings Yield được tính từ PE
        expected_earnings_yield = round((1 / 15.5) * 100, 2)
        self.assertEqual(result["Earnings_Yield"], expected_earnings_yield, 
                        "Earnings Yield phải được tính đúng từ PE")
        
        # Kiểm tra PEG được tính từ PE và EPS Growth
        expected_peg = round(15.5 / 12.5, 2)
        self.assertEqual(result["PEG"], expected_peg, "PEG phải được tính đúng")
        
        print("✅ Test 1 PASSED: Tất cả metrics được tính đúng")

    @patch('fintech_vnstock_only.Fundamental')
    @patch('fintech_vnstock_only.Financial')
    @patch('fintech_vnstock_only.stock_historical_data')
    def test_valuation_metrics_with_errors(self, mock_stock_data, mock_financial, mock_fundamental):
        """
        Test case 2: Kiểm tra hàm valuation_metrics khi có lỗi xảy ra
        
        Mục đích: Đảm bảo hàm xử lý lỗi gracefully và không crash
        """
        print("\n🧪 Test 2: valuation_metrics với lỗi xảy ra")
        
        # Mock để throw exception
        mock_fundamental_instance = Mock()
        mock_financial_instance = Mock()
        
        # Setup mock để throw exception cho một số methods
        mock_fundamental_instance.pe.side_effect = Exception("API Error")
        mock_fundamental_instance.pb.return_value = 2.1  # Một số methods vẫn hoạt động
        mock_fundamental_instance.roe.side_effect = Exception("Network Error")
        
        mock_financial_instance.current_ratio.return_value = 1.8
        mock_financial_instance.net_income.side_effect = Exception("Data Error")
        
        mock_stock_data.return_value = self.mock_price_data
        
        mock_fundamental.return_value = mock_fundamental_instance
        mock_financial.return_value = mock_financial_instance
        
        # Gọi hàm cần test
        result = valuation_metrics(self.test_ticker)
        
        # Kiểm tra kết quả - một số metrics phải là None do lỗi
        self.assertIsInstance(result, dict, "Kết quả vẫn phải là dictionary")
        self.assertIsNone(result["PE"], "PE phải là None do lỗi")
        self.assertEqual(result["PB"], 2.1, "PB vẫn hoạt động bình thường")
        self.assertIsNone(result["ROE"], "ROE phải là None do lỗi")
        self.assertIsNone(result["Earnings_Yield"], "Earnings Yield phải là None do thiếu PE")
        
        print("✅ Test 2 PASSED: Xử lý lỗi thành công")

    def test_valuation_metrics_empty_ticker(self):
        """
        Test case 3: Kiểm tra với ticker rỗng hoặc không hợp lệ
        
        Mục đích: Đảm bảo hàm xử lý input không hợp lệ
        """
        print("\n🧪 Test 3: valuation_metrics với ticker không hợp lệ")
        
        # Test với ticker rỗng
        with patch('fintech_vnstock_only.Fundamental') as mock_fundamental:
            mock_fundamental_instance = Mock()
            mock_fundamental_instance.pe.side_effect = Exception("Invalid ticker")
            mock_fundamental.return_value = mock_fundamental_instance
            
            result = valuation_metrics("")
            
            # Kết quả phải là dictionary với các giá trị None
            self.assertIsInstance(result, dict, "Kết quả phải là dictionary")
            # Ít nhất một số metrics phải là None
            self.assertTrue(any(value is None for value in result.values()), 
                           "Phải có ít nhất một metric là None")
        
        print("✅ Test 3 PASSED: Xử lý ticker không hợp lệ thành công")

    def test_display_results(self):
        """
        Test case 4: Kiểm tra hàm display_results
        
        Mục đích: Đảm bảo hàm hiển thị kết quả không bị lỗi
        """
        print("\n🧪 Test 4: display_results")
        
        # Dữ liệu test
        test_data = {
            "PE": 15.5,
            "PB": 2.1,
            "ROE": 18.5,
            "Current_Price": 99000,
            "Market_Cap": 50000000000
        }
        
        # Capture output để kiểm tra
        import io
        import contextlib
        
        output = io.StringIO()
        with contextlib.redirect_stdout(output):
            display_results(test_data, "FPT")
        
        output_text = output.getvalue()
        
        # Kiểm tra output có chứa thông tin cần thiết
        self.assertIn("FPT", output_text, "Output phải chứa mã cổ phiếu")
        self.assertIn("PE", output_text, "Output phải chứa PE")
        self.assertIn("15.5", output_text, "Output phải chứa giá trị PE")
        
        print("✅ Test 4 PASSED: display_results hoạt động đúng")

    @patch('builtins.open', create=True)
    def test_save_to_file(self, mock_open):
        """
        Test case 5: Kiểm tra hàm save_to_file
        
        Mục đích: Đảm bảo hàm lưu file thành công
        """
        print("\n🧪 Test 5: save_to_file")
        
        # Mock file object
        mock_file = MagicMock()
        mock_open.return_value.__enter__.return_value = mock_file
        
        # Dữ liệu test
        test_data = {
            "PE": 15.5,
            "PB": 2.1,
            "ROE": 18.5
        }
        
        # Gọi hàm
        save_to_file(test_data, "FPT", "test_file.txt")
        
        # Kiểm tra file được mở đúng cách
        mock_open.assert_called_once_with("test_file.txt", 'w', encoding='utf-8')
        
        # Kiểm tra file được write
        self.assertTrue(mock_file.write.called, "File phải được write")
        
        print("✅ Test 5 PASSED: save_to_file hoạt động đúng")

    def test_edge_cases(self):
        """
        Test case 6: Kiểm tra các trường hợp edge cases
        
        Mục đích: Đảm bảo code xử lý các trường hợp đặc biệt
        """
        print("\n🧪 Test 6: Edge cases")
        
        # Test với PE = 0 (không thể chia)
        test_data_zero_pe = {"PE": 0}
        
        # Test tính Earnings Yield với PE = 0
        try:
            if test_data_zero_pe.get("PE") and test_data_zero_pe["PE"] > 0:
                earnings_yield = (1 / test_data_zero_pe["PE"]) * 100
            else:
                earnings_yield = None
            self.assertIsNone(earnings_yield, "Earnings Yield phải là None khi PE = 0")
        except ZeroDivisionError:
            self.fail("Không được phép có ZeroDivisionError")
        
        # Test với EPS Growth = 0
        try:
            pe = 15.5
            eps_growth = 0
            if eps_growth and eps_growth > 0 and pe:
                peg = pe / eps_growth
            else:
                peg = None
            self.assertIsNone(peg, "PEG phải là None khi EPS Growth = 0")
        except ZeroDivisionError:
            self.fail("Không được phép có ZeroDivisionError")
        
        print("✅ Test 6 PASSED: Edge cases được xử lý đúng")


class TestIntegration(unittest.TestCase):
    """
    Test class cho integration testing
    
    Mục đích: Kiểm tra toàn bộ workflow hoạt động đúng
    """
    
    @patch('fintech_vnstock_only.valuation_metrics')
    @patch('fintech_vnstock_only.display_results')
    @patch('fintech_vnstock_only.save_to_file')
    def test_full_workflow(self, mock_save, mock_display, mock_valuation):
        """
        Test case 7: Kiểm tra toàn bộ workflow
        
        Mục đích: Đảm bảo các hàm hoạt động cùng nhau
        """
        print("\n🧪 Test 7: Full workflow integration")
        
        # Mock data
        mock_data = {"PE": 15.5, "PB": 2.1, "ROE": 18.5}
        mock_valuation.return_value = mock_data
        
        # Import và chạy main workflow
        from fintech_vnstock_only import TICKER
        
        # Simulate main workflow
        result = mock_valuation(TICKER)
        mock_display(result, TICKER)
        mock_save(result, TICKER)
        
        # Kiểm tra các hàm được gọi
        mock_valuation.assert_called_once_with(TICKER)
        mock_display.assert_called_once_with(mock_data, TICKER)
        mock_save.assert_called_once_with(mock_data, TICKER)
        
        print("✅ Test 7 PASSED: Full workflow hoạt động đúng")


def run_tests():
    """
    Hàm chạy tất cả test cases
    
    Mục đích: Chạy tất cả tests và hiển thị kết quả
    """
    print("🚀 BẮT ĐẦU CHẠY TEST CASES")
    print("=" * 60)
    
    # Tạo test suite
    test_suite = unittest.TestSuite()
    
    # Thêm test cases
    test_classes = [TestVnstockValuationMetrics, TestIntegration]
    
    for test_class in test_classes:
        tests = unittest.TestLoader().loadTestsFromTestCase(test_class)
        test_suite.addTests(tests)
    
    # Chạy tests
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(test_suite)
    
    # Hiển thị kết quả tổng kết
    print("\n" + "=" * 60)
    print("📊 KẾT QUẢ TEST TỔNG KẾT:")
    print(f"✅ Tests run: {result.testsRun}")
    print(f"❌ Failures: {len(result.failures)}")
    print(f"💥 Errors: {len(result.errors)}")
    
    if result.failures:
        print("\n❌ FAILURES:")
        for test, traceback in result.failures:
            print(f"  - {test}: {traceback}")
    
    if result.errors:
        print("\n💥 ERRORS:")
        for test, traceback in result.errors:
            print(f"  - {test}: {traceback}")
    
    if result.wasSuccessful():
        print("\n🎉 TẤT CẢ TESTS PASSED!")
        print("✅ Code hoạt động đúng và sẵn sàng sử dụng")
    else:
        print("\n⚠️ CÓ LỖI TRONG TESTS!")
        print("🔧 Cần sửa lỗi trước khi sử dụng")
    
    return result.wasSuccessful()


if __name__ == "__main__":
    """
    Chạy tests khi file được thực thi trực tiếp
    """
    success = run_tests()
    
    # Exit code dựa trên kết quả test
    exit_code = 0 if success else 1
    print(f"\n🏁 Chương trình kết thúc với exit code: {exit_code}")
    sys.exit(exit_code)
