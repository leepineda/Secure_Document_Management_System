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

MAY 26
---
Made add documents  (no alert, no delete)

Realizations
As i was watching reels and i saw a reel sayin Active Directory, has default read access to almost the entire database. And they use Bloodhound to spam LDAP queries to collect data, mapping out how compromised account can jump from machine to machine until it takes over a domain account.

I said why does this matter to me, I have RBAC on my end — but Bloodhound doesn't touch the app layer at all. It operates at the network and machine level. If the machine my app is running on is compromised, they can just dump the db, read the .env file, or connect to MySQL directly. My access controls never even run. A control is only as strong as the layer it sits on.

IT mainly focuses on the availability of things making sure they work, and the Sec guys try to make everything secure.

- The IT guy writes a script to automatically back up user files every night, and to make sure they dont hit the Access Denied they just gave the script domain admin privilege, now it works perfectly
- The Sec guy sees a random script running with full admin rights and blocks it and removes the privilege
- The night the backup didnt work because the script is stripped of of its privilege because of sec

 In tech in order to avoid things like this we need balance, It's really challenging to make a system secure while it also not being hard to use since security introduces friction. Security-Usability Trade-off
 In Zero trust we always verify that's what it is, but in real systems do we do MFA every time? That's gonna be a nightmare to use. And also not doing this check can also introduce a lot of risk back then if youre logged in you can do anything, we need balance for this things.

 I learned today that a system is basically un-operatable if its too strict, we need things like Prevention, and Detection
, and Behavioral Security... we need context.

Every security decision made, affects the user in some way or the other so I'll always keep that in mind.
The best example I can think of regarding this topic is Login sessions or cookies, we use cookies so when a user logs in and they close the tab and after some time they come back, we don't make them login again because we remember the session and making that session secure.  
And I also think session times depend on what we're building, we don't want to timeout on facebook every 15 minutes of inactivity.
And I also think it refreshes, for example on Facebook, we dont typically have the session ended every time. It takes days, as opposed to a system that handles confidential things, we need to have a lower tolerance of sessions e.g 10 mins of inactivity.

I also think this is what netflix and youtube, spotify uses. Maybe not all for security reasons
Netlix pops out the "Are you still watching?" because what if they fell asleep, theyre gonna burn data if they dont stop, but this doesnt happen all the time, I think they also have a user data they get for example a user watches typically from 10pm to 1 am, even tho the session or the alert activates every two hours because they are still on their usual time of watching it doesn't pop up and doesn't interrupt, but if they pass a certain treshhold thats quite unusual like they typicaly stop watching at 1am, but the video is still playing at 2am, now the alert comes in, just my random thoughts actually. 

I want to make something that have this I know it's challenging, once i finish this Im gonna try to do it, I hope this path wont bring the end of me. 

MAY 27
---
Added role check on app layer using session cookies when user deletes if != admin cant = delete, also introduced soft deletes
need to implement checks so deleted users cant show up on the index, if theyre deleted they cant show up on regular users