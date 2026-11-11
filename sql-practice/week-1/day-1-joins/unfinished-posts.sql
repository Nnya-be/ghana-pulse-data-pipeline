SELECT pa.part, pa.assembly_step 
FROM parts_assembly AS pa
WHERE pa.finish_date ISNULL;