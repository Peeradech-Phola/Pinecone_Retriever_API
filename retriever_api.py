import os
import dotenv
from pinecone import Pinecone
import pandas as pd
from fastapi import APIRouter
from fastapi.responses import JSONResponse, FileResponse
from io import BytesIO
import tempfile

router = APIRouter(prefix="/api")

# โหลด environment variables
dotenv.load_dotenv()
pc = Pinecone(api_key=os.getenv("PINECONE_API_KEY"))
index = pc.Index(os.getenv("PINECONE_INDEX_NAME"))

@router.get("/retrieve/{filename}")  # ใช้ path parameter
async def retrieve_data(
    filename: str,  # รับ filename จาก URL path
    format: str = "xlsx"  # default format เป็น xlsx
):
    try:
        namespace = os.getenv("PINECONE_NAMESPACE")
        
        # ค้นหาข้อมูลจาก Pinecone ด้วย filter
        response = index.query(
            vector=[1] * 1024,
            top_k=10000,
            namespace=namespace,
            include_metadata=True,
            filter={
                "filename": {"$eq": filename}
            }
        )
        
        # ดึงข้อมูลทั้งหมดจาก metadata โดยตรง
        data = [match.metadata for match in response.matches]
        
        if not data:
            return JSONResponse(
                status_code=404,
                content={"error": f"No data found for filename: {filename} in namespace: {namespace}"}
            )

        # สร้าง DataFrame
        df = pd.DataFrame(data)

        # เช็ค format และส่งผลลัพธ์
        if format.lower() == "json":
            return JSONResponse(content=df.to_dict(orient="records"))
            
        elif format.lower() == "csv":
            # สร้างไฟล์ชั่วคราวสำหรับ CSV
            with tempfile.NamedTemporaryFile(delete=False, suffix='.csv', mode='w', encoding='utf-8') as tmp:
                df.to_csv(tmp.name, index=False, encoding='utf-8')
                return FileResponse(
                    tmp.name,
                    media_type="text/csv",
                    filename=f"pinecone_output_{filename}.csv"
                )
        
        else:  # xlsx format (default)
            # สร้างไฟล์ชั่วคราวสำหรับ Excel
            with tempfile.NamedTemporaryFile(delete=False, suffix='.xlsx') as tmp:
                df.to_excel(tmp.name, index=False, engine='openpyxl')
                return FileResponse(
                    tmp.name,
                    media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                    filename=f"pinecone_output_{filename}.xlsx"
                )

    except Exception as e:
        print(f"Error: {str(e)}")  # เพิ่ม print เพื่อ debug
        return JSONResponse(
            status_code=500,
            content={"error": str(e)}
        )

# เพิ่ม route สำหรับการตรวจสอบสถานะ
@router.get("/status")
async def check_status():
    try:
        namespace = os.getenv("NAMESPACE")
        response = index.query(
            vector=[1] * 1024,
            top_k=1,
            namespace=namespace,
            include_metadata=True
        )
        return {"status": "ok", "message": "Connected to Pinecone successfully"}
    except Exception as e:
        return {"status": "error", "message": str(e)}