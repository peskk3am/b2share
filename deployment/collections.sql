-- id, collection name, search parameter
INSERT INTO collection VALUES (100,'Generic','980:"Generic"',NULL,NULL);
INSERT INTO collection VALUES (101,'Linguistics','980:"Linguistics"',NULL,NULL);
-- I don't know what the forth value is. First is parent collection (1 should
-- be site collection), second is child collection. Third I assume is "regular"
-- or "virtual" relationship but I'm not sure what this means...
INSERT INTO collection_collection VALUES (1,100,'r',60);
INSERT INTO collection_collection VALUES (1,101,'r',40);
