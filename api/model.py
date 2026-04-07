import json, os
from supabase import create_client

def handler(request):
    try:
        # model_id is everything after /api/model/
        path     = request["path"]
        model_id = path.split("/api/model/", 1)[-1].strip("/")

        if not model_id:
            return {"statusCode": 400, "body": json.dumps({"error": "model_id required"})}

        sb   = create_client(os.environ["SUPABASE_URL"], os.environ["SUPABASE_ANON_KEY"])
        meta = sb.table("models").select("*").eq("model_id", model_id).execute()

        if not meta.data:
            return {
                "statusCode": 404,
                "headers": {"Content-Type": "application/json"},
                "body": json.dumps({"error": f"Model not found: {model_id}"})
            }

        res  = sb.table("latest_results").select("*").eq("model_id", model_id).execute()
        code = sb.table("model_code").select("*").eq("model_id", model_id).execute()

        return {
            "statusCode": 200,
            "headers": {"Content-Type": "application/json", "Access-Control-Allow-Origin": "*"},
            "body": json.dumps({
                "model":   meta.data[0],
                "results": res.data or [],
                "code":    code.data or [],
            })
        }
    except Exception as e:
        return {
            "statusCode": 500,
            "headers": {"Content-Type": "application/json"},
            "body": json.dumps({"error": str(e)})
        }
