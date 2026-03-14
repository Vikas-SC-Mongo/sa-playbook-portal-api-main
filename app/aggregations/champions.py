# app/db/pipelines/champions_pipeline.py

champions_aggregation_pipeline = [
    {
        "$addFields": {
            "totalScore": {
                "$sum": {
                    "$map": {
                        "input": "$qualifications",
                        "as": "q",
                        "in": {
                            "$size": {
                                "$filter": {
                                    "input": {"$objectToArray": "$$q"},
                                    "as": "field",
                                    "cond": {
                                        "$and": [
                                            {"$ne": ["$$field.k", "question"]},
                                            {"$eq": ["$$field.v", True]}
                                        ]
                                    }
                                }
                            }
                        }
                    }
                }
            }
        }
    },
    {
        "$sort": {"totalScore": -1}
    }
]
