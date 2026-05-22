Making my way to security

To be honest this flask_mysql_app is just a small proj for me to understand how flask works on python, since this is what we are
using on our case study so I tried to make a simple app that connects to a mysql database a simple get post and just to understand
routes, and I made a repo on github to just try to make things work, know how to git add . and small version control.

This is also where I learned about environment variables that WE SHOULD'NT HARCODE PASSWORDS OR ANYTHING THAT COULD COMPROMISE
THE SYSTEM. Tho this has not all been me, I have a great teacher and the reason why I'm doing all this is because I've been 
inspired and I wanna know how to create secure systems, although I know of some things like RBAC and Principle of Least Priviledge
Etc... I still haven't implemented it on a real system nor even tried it

First day i made a simple app that just connects to a database in my case i used MySQL Maria DB, and I made some tables
that showed the data and simple prepared statements, and i actually hardcoded my password lol i still used root and didn't
make a new user (my teacher's gon get mad lmao) and i think i dont remember what happened exactly after that, maybe i refactored
my .gitignore since it contained too many files, and added a requirements file??

MAY 15, 2026
------------
This is where I made my mock database containing of 3 tables user, roles, and user_roles and I tried to use SQLAlchemy an ORM
but I didn't quite understood it so i reverted to using prepared statements first. I also looked at my code to
automatically assign a default role when adding a new user basically getting the hang of things.

MAY 16, 2026
------------
I added a simple SQL file that showed my database creation using raw sql so I have mock data, some users on my test app i added
using the no css UI lol.

This is where I also learned about GHOST USERS when a query cuts midway like the database got shutdown the process might not be saved worse may be incomplete, So i used transaction equivalent a try catch logic so that it only commits it when all the functions are done if it isnt done it rollsback like nothing happened

MAY 17, 2026 
------------
This is probably the biggest and the most humbling experience I had as of the creation, I was trynna use RBAC and i thought to myself, what if I just do stored procedures for everything and just make a user that can execute it? I sounded so proud like that's bulletproof to sql injections, but then if we scale things RBAC alone won't cut it and stored procedures won't cut it alone, so as I was scrolling YouTube, I stumbled upon this video titled RBAC vs ABAC by IBM Technology.
reference here: https://youtu.be/rvZ35YW4t5k?si=gR4FwxZoCp4TDKUI

And it introduced me to one step further from RBAC it's ABAC and that's why i also modified my sql tables to add trust_level and 
account status, to help me prepare how to navigate this new knowledge. It's basically a much stricter than RBAC and I also 
got introduced to security architecture that's why I made a pdp.py or Policy Decision Point  and I also learned about the concept
of Policy Enforcement Point the workflow that i discovered is PEP > Context > PDP > DB Execution, this checks a lot of things
but I told myself since if i create a PDP and this functions on the main app like one file one app, wouldnt it be worthless if
an attacker compromised the app itself? No? I'll keep that in mind but I'll try to do this first on the app, and ill also be
learning docker and railway so i can host not just on localhost. I also haven't done a simple login check and register check those are my next steps to try and use the access controls i've been learning, I also left my home and search routes open connections but don't use a try/finally structure like my add route, and also i need to watch out about that debug true on my code, illlook into it later

MAY 18 2026 WHERE I'm at and where I wanna be
------------
I want to be a security first person to be able to transform my knowledge into real things and not just all bark no bite
Right now I can't do stored procedures and I still struggle with joins and how to implement things, to be honest I'm lost 
I dont know where im heading but Ill do my best to show up every day i have the theories on my head i wanna transform and 
actually use them not just think

MAY 19 2026
------------
Changed the search and delete route to use try/finally and updated the debug=True to False, and tried to do some joins.
nothing much happened today, maybe next time i'd make a simple login page with a hash to try my access controls. I have an 
idea that's been bugging me for a while but i think im still not ready for it is for my app to implement a WAL since what if
the database goes down and a transaction got cut off i want to be able to go into 11:58 and see the lost query? data? 
i dont know what its called, my thoughts was before i execute a query i will send a text of that query on a log file lmaoo 
and also implement database encryption on the db itself because what if the db got compromised they can just dump a .db and
theyll see all data and thats BADDD fr fr and also i should add some RLS my teacher said that also that you dont want someone
to see what's not theirs my teacher the bomb fr

MAY 20 2026
------------
I encountered a problem, since i only designed three tables users, roles, and user_roles, I didn't make way for a register function
so i might overhaul the entire database, I mean that's the first thing we actually write down the tables and schemas first and
normalize them, but i was sidetracked on doing RBAC and ABAC i completely forgot we need more tables so that's on me, im gonna 
mark this on my mind to first make the tables that handle register, login, auth and things so i dont have to refactor again, 
I made a simple html file that registers but because the db isnt configured i might need to tweak and add it a little, but that's
enough for today, been tired cuz been working all day tiring, still a good hurdle for me to overcome

MAY 21 2026
-----------
I have a very huge huge hurdle, my database schema wont hold up, im currently trying to design it
My schema is absolute dogshit, like what
I think ill make an ERD first so i can map this all out, my thoughts and maybe even schemas and things, i need some time i said i need to tweak something a little but its not a little tweak 
I wanna answer on my database Who are you? What are ya trynna do? Is you gon rob me or what? Evidence?? huhh
man why did i think three tables was enough for this aint no way

--and also a quick note from my notes app from the phone--

So I've been wrestling with joins, and i had a thought that JOIN and ON are always connected, and the table that we apply to FROM table is basically what we SELECT table.first_table, if we select a column on a table, what we selected is what table we should add on the FROM clause. Okay things changed i learned that it doesn't matter the order of the tables as long as what you're selecting is included in the FROM or JOIN 

MAY 22 2026
-----------
Nothing much happened today, just created the schema for the new database and sql, I'm gonna update my routes next and get back in track.