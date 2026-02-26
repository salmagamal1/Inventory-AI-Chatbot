import re

def is_safe_sql(sql: str) -> bool:
    """
    Security guard to ensure the AI only runs read-only SELECT queries.
    Rejects any query containing dangerous manipulation keywords.
    """
    if not sql:
        return False
        
    cleaned_sql = sql.strip().upper()
    
    # Rule 1: It MUST be a SELECT query
    if not cleaned_sql.startswith("SELECT"):
        return False
        
    # Rule 2: It MUST NOT contain any destructive keywords
    dangerous_words = [
        r'\bDROP\b', r'\bDELETE\b', r'\bUPDATE\b', r'\bINSERT\b', 
        r'\bALTER\b', r'\bTRUNCATE\b', r'\bEXEC\b', r'\bEXECUTE\b', r'\bCREATE\b'
    ]
    
    for word in dangerous_words:
        if re.search(word, cleaned_sql):
            return False
            
    return True