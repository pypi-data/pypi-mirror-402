from kurra.sparql import query

q = """
    SELECT * 
    WHERE {
        GRAPH ?g {
            ?s ?p ?o
        }
    }
    """

q2 = "ADD <http://minimal1> TO <http://minimal1d>"

print(
    query(
        "http://localhost:7200/repositories/test2",
        q
    )
)