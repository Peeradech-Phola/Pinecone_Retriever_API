import os
import dotenv
from pinecone import Pinecone
import pandas as pd
from fastapi import APIRouter
from fastapi.responses import JSONResponse, FileResponse
from io import BytesIO
import tempfile

router = APIRouter(prefix="/api")

# Load environment variables
dotenv.load_dotenv()
pc = Pinecone(api_key=os.getenv("PINECONE_API_KEY"))
index = pc.Index(os.getenv("PINECONE_INDEX_NAME"))

@router.get("/retrieve/{filename}")
async def retrieve_data(
    filename: str,
    format: str = "xlsx"
):
    try:
        namespace = os.getenv("PINECONE_NAMESPACE")

        # Query Pinecone index for matching data
        response = index.query(
            vector=[1] * 1024,
            top_k=10000,
            namespace=namespace,
            include_metadata=True,
            filter={
                "filename": {"$eq": filename}
            }
        )

        data = [match.metadata for match in response.matches]

        # If no data is found, return a 404 error
        if not data:
            return JSONResponse(
                status_code=404,
                content={"error": f"No data found for filename: {filename} in namespace: {namespace}"}
            )

        extracted_data = []
        for item in data:
            text_content = item.get("text", "")

            try:
                # Split the text content by the third colon
                parts = text_content.split(":", 3) 
                if len(parts) == 4:
                    no = parts[1].strip().split()[0] 
                    question = parts[2].strip()
                    question_colunm = parts[1].strip().replace(no, "").strip()  
                    answer = ":".join(parts[3:]).strip() 
                    
                    if item == 0:  
                        question = question + ": " + parts[2].strip()

                    extracted_data.append({
                        "No": no,
                        "question " + question_colunm: question, 
                        "answer": answer
                    })

            
            except Exception as e:
                print(f"Failed to split text content: {str(e)}")

        # If no valid data was extracted, return a 404 error
        if not extracted_data:
            return JSONResponse(
                status_code=404,
                content={"error": "No valid data extracted from text field"}
            )

        # Create a DataFrame from the extracted data
        df = pd.DataFrame(extracted_data)
        df['No'] = pd.to_numeric(df['No'], errors='coerce') 
        df = df.sort_values(by='No') 

        # Return data in the requested format
        if format.lower() == "json":
            return JSONResponse(content=df.to_dict(orient="records"))
        elif format.lower() == "csv":
            with tempfile.NamedTemporaryFile(delete=False, suffix='.csv', mode='w', encoding='utf-8') as tmp:
                df.to_csv(tmp.name, index=False, encoding='utf-8')
                return FileResponse(
                    tmp.name,
                    media_type="text/csv",
                    filename=f"{filename}"
                )
        else:
            with tempfile.NamedTemporaryFile(delete=False, suffix='.xlsx') as tmp:
                df.to_excel(tmp.name, index=False, engine='openpyxl')
                return FileResponse(
                    tmp.name,
                    media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                    filename=f"{filename}"
                )

    except Exception as e:
        print(f"Error: {str(e)}")
        return JSONResponse(
            status_code=500,
            content={"error": str(e)}
        )
