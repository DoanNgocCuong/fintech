## Cách sử dụng VNStock MCP Server

### Bước 1: Cài đặt

**Cài đặt từ PyPI** (phiên bản không chính thức):

```bash
pip install vnstock-mcp-server
```

Sau khi cài đặt, chạy server bằng lệnh :[1]

```bash
vnstock-mcp-server
```

**Cài đặt từ GitHub** (phiên bản chính thức):

```bash
git clone https://github.com/gahoccode/vnstock-mcp
cd vnstock-mcp
pip install -r requirements.txt
```

### Bước 2: Cấu hình Claude Desktop

**Mở file cấu hình** của Claude Desktop :[2][3]

- **MacOS**: `~/Library/Application Support/Claude/claude_desktop_config.json`
- **Windows**: `%APPDATA%\Claude\claude_desktop_config.json`

**Thêm cấu hình** VNStock MCP Server vào file JSON :[4][5][2]

```json
{
  "mcpServers": {
    "vnstock": {
      "command": "vnstock-mcp-server"
    }
  }
}
```

Hoặc nếu sử dụng Python trực tiếp:

```json
{
  "mcpServers": {
    "vnstock": {
      "command": "python",
      "args": ["-m", "vnstock_mcp_server"]
    }
  }
}
```

### Bước 3: Khởi động lại Claude Desktop

**Thoát hoàn toàn** và khởi động lại Claude Desktop để tải cấu hình mới. Sau khi khởi động lại, biểu tượng MCP server sẽ xuất hiện ở góc dưới bên phải của ô nhập tin nhắn.[2][4]

### Bước 4: Sử dụng trong Claude

**Kiểm tra kết nối** bằng cách hỏi Claude: "What MCP tools are available right now?". Các công cụ từ VNStock MCP Server sẽ hiển thị trong danh sách.[4]

**Ví dụ câu lệnh** để sử dụng :[6][7]

- "Lấy giá cổ phiếu VIC từ ngày 01/01/2024 đến 31/03/2024"
- "Cho tôi xem dữ liệu lịch sử của VN30F1M"
- "Danh sách các cổ phiếu có thanh khoản cao nhất"

### Cấu hình tùy chỉnh

**Tạo file JSON** để chỉ định các mã cổ phiếu cần theo dõi :[5][7]

```json
{
  "stocks": ["VIC", "VNM", "HPG", "VCB"]
}
```

**Chỉ định file cấu hình** khi khởi động server với tùy chọn `--config` :[5]

```bash
vnstock-mcp-server --config /path/to/config.json
```

---


1. https://lobechat.com/discover/mcp/maobui2907-vnstock-mcp-server?activeTab=deployment
2. https://modelcontextprotocol.io/docs/develop/connect-local-servers
3. https://support.claude.com/en/articles/10949351-getting-started-with-local-mcp-servers-on-claude-desktop
4. https://skywork.ai/blog/how-to-install-computer-use-mcp-server-claude-desktop-guide/
5. https://lobechat.com/discover/mcp/maobui2907-vnstock-mcp-server?hl=it-IT
6. https://github.com/sverze/stock-market-mcp-server
7. https://github.com/chatmcp/mcpso/issues
8. https://www.forum.vnpro.org/forum/ccna%C2%AE/ai-for-everyone/431432-chia-s%E1%BA%BB-k%E1%BA%BFt-n%E1%BB%91i-mcp-server-v%E1%BB%9Bi-claude-desktop-ch%E1%BB%89-trong-v%C3%A0i-ph%C3%BAt-%E2%80%8B
9. https://www.youtube.com/watch?v=RhTiAOGwbYE
10. https://realpython.com/python-mcp/
11. https://www.youtube.com/watch?v=C1cAFLMNmyk
12. https://dev.to/mrzaizai2k/building-an-mcp-server-with-fastapi-mcp-for-stock-analysis-a-step-by-step-guide-de6
13. https://github.com/financial-datasets/mcp-server
14. https://www.reddit.com/r/MCPservers/comments/1lw1jwe/how_do_you_actually_set_up_an_mcp_server_on/
15. https://www.youtube.com/watch?v=VGimD-Q0wLw
16. https://mastra.ai/guides/guide/notes-mcp-server
17. https://www.linkedin.com/pulse/tutorial-build-simple-mcp-server-claude-desktop-janakiram-msv-qn9nc
18. https://www.youtube.com/watch?v=jLM6n4mdRuA
19. https://brightdata.com/blog/ai/web-scraping-with-mcp
20. https://www.reddit.com/r/LocalLLaMA/comments/1jz2cj6/building_a_simple_mcp_server_step_by_step_guide/
21. https://modelcontextprotocol.io/examples

---

# DÙNG TRONG CODE APP.py được ko ?


1. [https://viblo.asia/p/fastapi-mcp-la-gi-tich-hop-ai-de-dang-cho-cac-api-fastapi-cua-ban-GAWVpqZ3405](https://viblo.asia/p/fastapi-mcp-la-gi-tich-hop-ai-de-dang-cho-cac-api-fastapi-cua-ban-GAWVpqZ3405)
2. [https://mcpshowcase.com/blog/rest-api-to-python-mcp-server](https://mcpshowcase.com/blog/rest-api-to-python-mcp-server)
3. [https://modelcontextprotocol.io/docs/develop/build-server](https://modelcontextprotocol.io/docs/develop/build-server)
4. [https://www.perplexity.ai/search/xnoapi-https-xnoapi-readthedoc-u4QM8IbJSlWSLFfKOWtnGg](https://www.perplexity.ai/search/xnoapi-https-xnoapi-readthedoc-u4QM8IbJSlWSLFfKOWtnGg)
5. [https://www.flowhunt.io/vi/blog/python-libs-for-mcp-server-development/](https://www.flowhunt.io/vi/blog/python-libs-for-mcp-server-development/)
6. [https://apidog.com/vi/blog/open-source-mcp-server-vi/](https://apidog.com/vi/blog/open-source-mcp-server-vi/)
7. [https://codelabs.developers.google.com/codelabs/cloud-run/how-to-deploy-a-secure-mcp-server-on-cloud-run?hl=vi](https://codelabs.developers.google.com/codelabs/cloud-run/how-to-deploy-a-secure-mcp-server-on-cloud-run?hl=vi)
8. [https://codelabs.developers.google.com/codelabs/cloud-run/use-mcp-server-on-cloud-run-with-an-adk-agent?hl=vi](https://codelabs.developers.google.com/codelabs/cloud-run/use-mcp-server-on-cloud-run-with-an-adk-agent?hl=vi)
9. [https://truetech.com.vn/model-context-protocol-mcp-la-gi-huong-dan-cai-dat-ung-dung-va-so-sanh-voi-api/](https://truetech.com.vn/model-context-protocol-mcp-la-gi-huong-dan-cai-dat-ung-dung-va-so-sanh-voi-api/)
10. [https://apidog.com/vi/blog/mcp-servers-explained-vi/](https://apidog.com/vi/blog/mcp-servers-explained-vi/)
11. [https://www.reddit.com/r/ClaudeAI/comments/1is94a7/i_analyzed_628_mcp_servers_with_claude_and_built/](https://www.reddit.com/r/ClaudeAI/comments/1is94a7/i_analyzed_628_mcp_servers_with_claude_and_built/)
12. [https://viblo.asia/p/8-mcp-server-ma-nguon-mo-ma-cac-nha-phat-trien-nen-su-dung-EvbLbK3oVnk](https://viblo.asia/p/8-mcp-server-ma-nguon-mo-ma-cac-nha-phat-trien-nen-su-dung-EvbLbK3oVnk)
13. [https://www.reddit.com/r/ChatGPTCoding/comments/1jd9lfa/learn_mcp_by_building_an_sql_ai_agent/](https://www.reddit.com/r/ChatGPTCoding/comments/1jd9lfa/learn_mcp_by_building_an_sql_ai_agent/)
14. [https://lobehub.com/vi-VN/mcp/jangjangji-mcp_test](https://lobehub.com/vi-VN/mcp/jangjangji-mcp_test)
15. [https://lobehub.com/vi-VN/mcp/yourusername-code-mcp](https://lobehub.com/vi-VN/mcp/yourusername-code-mcp)
16. [https://www.youtube.com/watch?v=ToOEOEcmtPM](https://www.youtube.com/watch?v=ToOEOEcmtPM)
17. [https://apidog.com/vi/blog/ollama-web-search-api-mcp-server-vi/](https://apidog.com/vi/blog/ollama-web-search-api-mcp-server-vi/)
18. [https://tuyendung.evotek.vn/30-y-tuong-mcp-server-day-suc-manh-kem-ma-nguon-hoan-chinh/](https://tuyendung.evotek.vn/30-y-tuong-mcp-server-day-suc-manh-kem-ma-nguon-hoan-chinh/)
19. [https://viblo.asia/p/danh-cho-nha-phat-trien-doc-lap-xay-dung-quy-trinh-lam-viec-hien-dai-voi-mcp-server-va-cong-cu-gjLN0eKw432](https://viblo.asia/p/danh-cho-nha-phat-trien-doc-lap-xay-dung-quy-trinh-lam-viec-hien-dai-voi-mcp-server-va-cong-cu-gjLN0eKw432)
20. [https://www.youtube.com/watch?v=wbD9--JAvzs](https://www.youtube.com/watch?v=wbD9--JAvzs)
21. [https://apidog.com/vi/blog/code-index-mcp-guide-vi/](https://apidog.com/vi/blog/code-index-mcp-guide-vi/)


---



## 🔧 Phân tích lỗi và giải pháp

Lỗi trong code là **FastMCP không hỗ trợ tham số `port` trực tiếp** khi sử dụng STDIO transport. MCP server mặc định sử dụng STDIO (Standard Input/Output) để giao tiếp, không phải HTTP với port.[1][2][3]

### Nguyên nhân chính

**Sai cú pháp**: `server.run(port=3001)` không đúng với STDIO transport. MCP server có hai loại transport :[4][2][1]

- **STDIO**: Giao tiếp qua stdin/stdout (mặc định, không cần port)
- **SSE**: Giao tiếp qua HTTP Server-Sent Events (cần port)

### Giải pháp 1: STDIO Transport (Khuyến nghị)

```python
from vnstock_mcp.server import server

if __name__ == "__main__":
    # Chạy với STDIO - không cần port
    server.run()
```

Đây là cách **chuẩn** cho MCP server kết nối với Claude Desktop.[3][1]

### Giải pháp 2: SSE Transport với Port

```python
from vnstock_mcp.server import server

if __name__ == "__main__":
    # Chỉ định transport SSE và port
    server.run(transport='sse', port=3001)
```

SSE transport cho phép kết nối qua HTTP, phù hợp với web applications.[2][4]

### Giải pháp 3: Tự tạo server với FastMCP

```python
from fastmcp import FastMCP
from vnstock import stock_historical_data

mcp = FastMCP(name="VNStockServer", port=3001)

@mcp.tool()
def get_stock_history(symbol: str, start_date: str, end_date: str) -> dict:
    """Lấy dữ liệu lịch sử cổ phiếu"""
    data = stock_historical_data(symbol, start_date, end_date)
    return {"success": True, "data": data.to_dict('records')}

if __name__ == "__main__":
    mcp.run()
```

Cách này cho **toàn quyền kiểm soát** server configuration.[2][3]

### Cài đặt dependencies

```bash
pip install fastmcp vnstock vnstock-mcp-server
```

### Kiểm tra và debug

Chạy file `debug_vnstock.py` để kiểm tra môi trường :[5]

```bash
python debug_vnstock.py
```

File này sẽ hiển thị các module đã cài đặt, phiên bản, và methods có sẵn .

### Cấu hình cho Claude Desktop

Với STDIO transport, thêm vào `claude_desktop_config.json` :[1][2]

```json
{
  "mcpServers": {
    "vnstock": {
      "command": "python",
      "args": ["vnstock_mcp_run_fixed.py"]
    }
  }
}
```

Lỗi chính là nhầm lẫn giữa STDIO và SSE transport khi gọi `run()` method
