MAY 24
---
As i was checking my sql database i saw the security logs show NULL for the deleted users, woulnt that be bad? i think i need a
archive for this, and as my teacher said we never delete things, we just archive them so, id look into that later
for now i made login route, incomplete pseudo code, ill finish it tomorrow including the HTML

trying to ground myself and not over engineer things, im gonna focus on the MVP for now and harden it later

MAY 25
---
I made the MVP, the login, register, add, search, delete, logout all works
added:
    sessions
    password hashing and checking

realizations: knowing how to secure a system is vastly different from actually making one, ive been so focused on things that don't really align with what im doing, I have RBAC, ABAC, etc etc... while i still didnt have an MVP

I've been overthinking a lot, and I don't even have a working system even the core loop isn't built and im worrying about ABAC and RBAC which is good but,  you just have to build the MVP and harden it, iteration, but there's a baseline you have to follow, parametrized sql, hashing sensitive data, API keys hidden, never use the root user, grant onlt select, update an insert on a user, these things are non negotiable on any given system thats the baseline, you dont need rate limiting on version 1, yes yiu can get DDOS but it doesnt cost as much as your passwords having been leaked and your database dropped because of an sql injection

Its good that im worrying about security this much but, thats my biggest weakness, i haven't even made a system, my focus should be on the most absolutely basics and the baseline or the mvp, until then i wont worry about things other than on the present bur always keep in mind about the non negotiables

Phase 1 secure it MVP should absolutely contain this

dont use plain text 
make.a new user grant it only select update insert never delete
parametrized sql
always wrap it with a try/finally
or transactions in sql

phase1.1 Add soft deletes
add security logs

added a documents viewer, no filtering yet — 
every authenticated user sees everything including confidential. 
that's the next thing to fix.