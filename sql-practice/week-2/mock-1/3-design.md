### Model Design
First the data would go to a place I would load the raw data to, let's call it a bronze layer here, I would load all the data that the provider has and would save it as a parquet file.

Later I would filter and perform check on it into a column storage and also perform the needed operations to make sure that the data is well structured. Let's call this the silver layer.

then I would now refine the table into a star schema and make sure that It is now ready to draw insights from it and also make sure that it is query optimized.

now if there is a rerun on the account, there wouldn't be a redownload of previous loaded data and if there is a corrected file then it would be ovverwritten and also I would name the file path in a way that duplicate ones wouldn't reappear since thier paths would already exist. Because I would keep a meta file that would load the parameters and the needed information with a hash from the file into it.

The 3 data quality checks that I would run would be, to check to see that all the days requested are downloaded and also check to see if the account balance reflects the money sent and recieved. Also I would check to see that the corrupted file would be reloaded to rewrite the old one. I would aslo check to see the transaction date correspond to the date the file was posted and that is if the user only post that days work.

I would check to see the date last loaded to know if it is past my scheduled time and the know that it is late,and I would rerun that day for the files on that day if the pipeline is broken the I would try trouble shooting by checking if the servers are down or the API contracts have been changed.