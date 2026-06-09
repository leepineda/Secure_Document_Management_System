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
- also need to update queries and decide what uses is_deleted TRUE or FALSE, normal users cant and shouldnt see deleted users, only certain people. how do I enforce authorization once, correctly, and everywhere reliably?

MAY 28 
---
added input validation on registration route, doesnt have any indicator if registration failed or completed, need to update and work on

MAY 29
---
## Learned:

- Learned that flash messages are global so we categorize them so they don't leak on other routes.
- Learned to store role sessions on login route, we select it from the database and stores the role and assigns to default if someone doesnt have a role so it acts as a fallback.
- Learned to use session.clear() at first i was doing session.pop() due to this i had to add the account_id and the role_name pop() so i used the session.clear to clear everything in one go.

## Added:

- Role store in sessions when logging in 
- Added in the logout to pop out the role name (made session.clear())
- Error messages showing correctly 
- Login session check on Search route
- Home route now doesn't display deleted accounts/documents
- Last logged in added on user_credentials


## Problems encountered:

- Flash message on home route leaking to registration
- Fix: removed the flash since if a user isnt on session they are automatically redirected to the login route

## Need fixing

- Login route uses huge if-else and security_logs don't log login attempts

MAY 31 
---
users can only access public files, moderators can access internal, admin can access confidential and top secret
I missed a lot of things, inverted login flow, flash messages still leaking, undefined variables, typos, connection commits missing, i saw some people use SAST tools and I think it wouldve helped me catch some of this errors, but some errors did need human review, the old login route is syntax correct but the logic is inverted. Also still learning proper documentation. I cannot be missing anything if it comes to security, that will be a nightmare so I'm gonna try to use tools for this


## Learned:
- Learned to always check logic of the routes/functions and how it always moves
- Learned to reject early, succeed late
- Learned to always handle every failure case first, success path is always last and unblocked
- Learned that some code are dead if the preliminary checks dont even let them execute
- Learned that Flask flash messages persist in the session until get_flashed_messages() is called, which clears them, if a page never calls it, they leak to the next page that does like my register route
- Learned that Url for uses function names, and not routes
- Learned about SAST, DAST, GitHub Advanced Security Bandit, Semgrep, etc... tools that let you help catch errors on codes, vulnerabilities, without manually looking for them
- Learned that ENUM columns take strings not integers,  different from BOOLEAN/TINYINT
- Learned that changelogs are permanent records, known issues move to fixed, never deleted
- Learned what CSRF is and why POST routes are vulnerable without tokens

## Problems encountered
- Inverted login, checks happen AFTER login
- User_role not assigned on session
- Login always redirected back to login because the path was blocked by the inverted status checks
- User checks suspended and pending never executes because of the status = "active"
- Last login always executes even if the login fails
- Flash messages on register route
- get_flashed_messages() called twice in register.html, second call always returned empty but was leaking because of the uncalled login flash messages

## Added:
- Flash messages on login
- Flash message categories
- Added checks on roles and what document they can access
- Added user_role assignment 

## Changed:
- Overhauled the login route to 
 check if user = exists, password = exists
 check status, suspended, pending, active
 if active select user
 select role
 add session for role and user
 updated last login 
- updated sql to default to "active" when registering

JUNE 1
---
added CSRF protection using Flask WTF (pip install Flask-WTF), it is actually easy to implement, just an import and updating the html files. Also we don't put a csrf check on GET routes only POST, PUT, DELETE, state changing or data manipulating methods only

Also thought about doing rate  limiting by adding an attribute on user_accounts to have login_attempts and lockout_until, but i wont a hacker just use multiple devices to fire? if they use multiple accounts and each only fire 1 request per IP Address the attempts just update to 1 per request and never hits the lockout, lockout is good if they try to brute force an account like the admin, or a specific user since every IP gets logged in the login_attempts but there's still something missing

I also still need to add better security logs and proper authorization on creating documents since everyone can create a document without any role checks

I also still need to clean the code and architecture, so much things could be improved like the role checks should just be decorators, id keep that all in mind

## Learned:
- CSRF Protection implementation
- CSRF is mainly used for data manipulating methods like POST, PUT, DELETE etc... and not GET methods

## Added:
- csrf token checks on every html/files

JUNE 2
---
Altered my user_accounts table to have login_attempts and lockout_until
This solves two things login attempts we check it so brute forcing one password we activate lockout_until
and lockout_until, on repeated guesses increases on time e.g 5mins -> 10 mins etc...

Wow a login is actually complicated, we need to update things like sessions in it, also clear sessions, add rate limiting and check status, update attempts, and the way the login flows is really important, we only do the most important things after they passed all the checks and even then we clear the session and assign a new one I thought logins are just checking if user exists and password match but no, it seems more complicated than I thought man, also more problems like this thing i implemented doesn't solve if the attacker uses 1000 different ip addresses, also lockouts are exponential right? on cellphones if you repeatedly try to unlock a phone 1 minute turns into 3 and 5 +++,

man now i know why everyone uses flask-login, or just use the framework for login and never do this manually lol

## Learned:
- Login's are not as easy as it sounds

# Added:
- login_attempts and lockout_until attributes on user_accounts

<details>
<summary> JUNE 3 — Login Security & DB Hardening</summary>

## JUNE 3 — Login Security & DB Hardening

Encountered a logic problem in the login route, instead of giving a fallback role when none is found, we now reject and redirect. Role assignment happens at registration, so a missing role means something broke or was bypassed on the system.

Also explored database security layering, limiting the app DB user to SELECT, INSERT, UPDATE only; restricting the audit log table to INSERT only. Thought through destructive operations like hard deletes, stored procedures help, but if the public app itself is compromised, a solution I think wold be good is a separate app that have a db user that has DELETE privileges like an admin, so the regular db user and the db user with more priviledge is also seperate.

My Professor introduced this concept, but building it myself is where I actually encountered how it's used.

# Learned:
- Learned that instead of having grace when an unexpected problem occurs, reject and redirect them, giving them a fallback is trusting them. If the system manages those things and if someone breaks it its worth keeping eye on, for example if someone enters without a role and try to login, that is an unexpected variable, we dont give them grace

- Learned that Security Logs are critically important, it is the first Incident Response baseline, if you dont have logs, you dont know what happened and by who, when, and what. Also append only is critical, you dont want someone inserting fake logs thats dangerous. Also logs need to also have different clusters, instead of a big security_logs table, we split them up to registration_logs, login_logs, activity_logs... good to keep in mind but that's for another day

- Also learned that schema decisions on the very first day is critical, changing a live table is gonna cost downtimes.

- Also learned about database migration, and database optimization.

- Also learned that application layer role checks and database layer privilege restrictions are separate concerns that reinforce each other,  the DB user having no DELETE isn't about restricting admin users, it's about limiting the damage if the application is compromised.

</details>

<details> 
<summary> JUNE 4 2026 Skipped</summary>
</details>

<details>
<summary> JUNE 5 2026 </summary>

## JUNE 5 Security Logs

I wanted to add what's considered as the baseline of Incident Response, logs, you can't respond on something you don't have an IDEA on. Logs depending on how you build it is like the CCTV, you see who did it, what they did, and when they did it. Logs should be immutable, no one can delete it, no one can change it, it's readable, and there's no manipulation. Logs give way to Log analysis, monitoring, identification, etc...

</details>

<details> 
<summary> JUNE 6 2026 </summary>

## JUNE 6 Login Logs

I learned that doing things like pasting one by one a block of code is gonna introduce indentation issues especially on python. Indentation is really important

# Learned:
- Knowing what to log are key to a good CCTV, if the logs are messy, the information that you can extract from that data is minimal.

</details>

<details> 
<summary> JUNE 7 2026</summary>

## JUNE 7 Additional Logs

Im contemplating whether i should add additional logs on my Registration, do I need to add more? An attack might come that guesses i dont know what its called but lets say someone knows an account, they might note them and try to attack that on the Login page no? I need to look more into that. 

Also my login filters if not user and redirects back, doesn't this introduce a new problem? but what problem? both the if not user and other things say invalid credentials? I saw people say that a hacker can try to use timings? on this so they know if something has an account even tho the message says invalid creds only

Okay i learned its called a Side Channel Attack i saw this video from MIT OpenCourseWare 16. Side-Channel Attacks 
here's the link https://youtu.be/3v5Von-oNUg?si=VnMSx_aueH9j-6HH
I need to re watch this a couple times to actually understand some concepts but it is a good thing to know, security isnt just locked in a layer, its how the system behaves huh
Basically crytopgraphic tools like scrypt takes time, and hackers can use that time to guess if a real user exists i think this is what my login misses, it redirects immediately at the slight error on if not user so the hacker can guess if a user exists with only that information, and if it takes more time like the user is real and they check the password they also know it

Wow how the system behaves can also be exploited, man I still don't know anything.

I think I'm gonna watch a lot of lectures from this day onwards, and ofc also implement them

even network bits can be exploited
</details>

<details>
<summary> JUNE 8 2026</summary>

## JUNE 8 2026 Privileges

So as I was washing dishes, I had a thought that, first do I really need to make an INSERT query every wrong action? Isn't that what triggers are for? And also revoking privileges, isn't it too time consuming to REVOKE all delete on the TABLES? and I said Isn't that why we have user roles? BUT, what if we DIDN'T revoke the DELETE on admin, and let's say we do, but WE didn't revoke the GRANT privilege, and now he can just GRANT DELETE on user, and also modify the security_logs to be DELETE able? wouldn't it all come crashing down? 

If the admin is compromised, if we don't lock him down, an ADMIN is the worst security threat we can have if we don't configure the things cleanly

Unrevoked privileges are high risk vulnerabilities.

</details>

<details>
<summary> JUNE 9 2026 </summary>

## JUNE 9 2026 Register Cleanup

I got sidetracked again, there are still lingering issues, now I'll fix the register route to also have what login does, proper logging on registration/ failed/ duplicate.
Critical flaw is the Log insert is on the transaction so if the transaction fails, we dont have a record so we fixed that.

My registration also doesn't have a rate limiter, but because we don't have a account attached to it it's not as easy to manage, Im gonna make it just check the IP address, but then it still wouldnt stop an attacker on using 1000 different IP maybe this is where WAF and CAPTCHA is used, dont mean I cant use them both no?, Ill note it.

</details>
