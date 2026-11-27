A mobile money app has customers, and each customer has a tier: basic, standard or premium. A customer's tier can change over time. The business wants a report of total transaction value by tier, where each transaction counts under the tier the customer had when the transaction happened.

Sketch the tables, a fact and its dimensions, with their main columns. Say what one row of the fact table is.
Explain how you'd store the tier, so the report stays correct after a customer moves from basic to premium.
Name one risk in your design, and how you'd test for it.


Ans: Since the app has tiers we would want to save the tiers that the users are on so that the report can have that.

So first the tables I would have are, the dim_customer(customer_id, customer_key, customer_name, customer_email, customer_phone) and all the relevant customer details will go here. Then I will store a dim date for the dates where transactions happend and when they moved to join which tier and all those dates. also I will keep a tier dimension which I would make it have a tier key, name, id and how they are charges in that teir and all those relevant things.

Then on the fact transaction table, I will keep the teir key as a type 2 dimension since we would want to report that as well and knowing the previous tier the users were is of good use. Then I will keep the customers key to reference the customer and also the date that each transaction occurs and the amount and all that as things that we can measure. 