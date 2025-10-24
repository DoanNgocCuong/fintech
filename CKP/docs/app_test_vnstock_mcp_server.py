# # app_test_vnstock_mcp_server.py
# from vnstock_mcp.server import server

# if __name__ == "__main__":
#     try:
#         print("🚀 Starting VNStock MCP Server...")
#         # ✅ ĐÚNG: Không truyền tham số không hỗ trợ
#         server.run()
#     except Exception as e:
#         print(f"❌ Error starting server: {e}")



# # app_test_vnstock_mcp_server.py
# from vnstock_mcp.server import server

# if __name__ == "__main__":
#     try:
#         print("🚀 Starting VNStock MCP Server with HTTP transport...")
#         # ✅ ĐÚNG: Dùng HTTP transport để có API endpoint
#         server.run(transport="http", host="127.0.0.1", port=8000)
#         print("📡 MCP API available at: http://localhost:8000/mcp/")
#     except Exception as e:
#         print(f"❌ Error starting server: {e}")


# app_test_vnstock_mcp_server.py
from vnstock_mcp.server import server
import logging

# Enable logging để debug
logging.basicConfig(level=logging.DEBUG)

if __name__ == "__main__":
    try:
        print("🚀 Starting VNStock MCP Server...")
        print("📡 Server will be available at: http://localhost:8000/mcp/")
        
        # Thử với HTTP transport
        server.run(transport="http", host="0.0.0.0", port=8000)
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

