"""Hand-written ticket scenarios for the generator.

Each scenario has a category, a priority that follows from the situation
described, an explicit tuple of roles that could plausibly report it, and a
list of (subject, body) variants. A subject and body are written as a pair,
so every variant is consistent with itself. Every role listed for a scenario
must fit every variant of it.

Text may use the placeholders {room}, {bldg} and {n}. The same values are
filled into the subject and the body of one ticket.

Priority meanings (see docs/architecture.md):
  P1  outage or safety issue affecting many people, or a blocked critical function
  P2  one person or small group fully blocked, no workaround
  P3  degraded or inconvenient, workaround exists
  P4  request, question or minor issue
"""

from dataclasses import dataclass
from typing import Tuple

CATEGORIES = (
    "account/access",
    "hardware",
    "software",
    "network",
    "MDM/device",
    "other",
)

PRIORITIES = ("P1", "P2", "P3", "P4")


@dataclass(frozen=True)
class Scenario:
    category: str
    priority: str
    roles: Tuple[str, ...]
    variants: Tuple[Tuple[str, str], ...]

    @property
    def capacity(self) -> int:
        """How many tickets this scenario can supply without repeating text."""
        return len(self.variants)


def _s(category, priority, roles, variants):
    return Scenario(category, priority, tuple(roles), tuple(tuple(v) for v in variants))


SCENARIOS = (
    # ------------------------------------------------------------------
    # account/access
    # ------------------------------------------------------------------
    _s("account/access", "P1", ("teacher", "special education teacher"), [
        ("Nobody can log in this morning",
         "Started around 7:30. Every teacher I have talked to in Building {bldg} gets "
         "'invalid credentials' on the sign-in page, even after retyping. Homeroom "
         "attendance is due in 15 minutes and none of us can get to it."),
        ("Staff sign-in is failing for everyone",
         "Is sign-in down? I tried my laptop and my phone, same error. The front office "
         "says it is happening to them too and the first bell is about to ring. "
         "Please call the office when you know anything."),
    ]),
    _s("account/access", "P1",
       ("teacher", "office manager", "vice principal", "counselor", "front office staff", "librarian"), [
        ("My email account is sending strange messages to the whole staff",
         "Several people have replied to me about an email I did not send. It has a link "
         "and says to verify my password. I think my account was taken over. I already "
         "changed my password but I do not know if that was enough. Staff are clicking "
         "it right now."),
        ("A colleague's email is sending a fake login link to all staff",
         "A message from a colleague's address went to the entire staff list asking us "
         "to confirm our login on an outside page. The person says they did not send it. "
         "About {n} people have already told me they clicked."),
    ]),
    _s("account/access", "P2", ("teacher", "special education teacher", "coach"), [
        ("Locked out of gradebook, grades due today",
         "I am locked out of the gradebook after too many tries. Report card grades are "
         "due by 4 today. I do not have my sign-in code with me. I need to be let back in "
         "this morning, there is no other way for me to enter them."),
        ("Cannot sign in to the gradebook",
         "gradebook says my account is locked. grades due end of day. please unlock asap"),
    ]),
    _s("account/access", "P2", ("principal", "vice principal", "office manager"), [
        ("New teacher has no accounts",
         "We have a new teacher in room {room} who started this morning. Nothing has been "
         "set up for them. No computer login, no email, no gradebook. HR said the paperwork "
         "went through last week. They are covering a class right now with nothing but a "
         "paper roster."),
        ("New hire started today and cannot log in to anything",
         "Our new aide's first day is today and the sign-in we were given says the account "
         "does not exist. Can you check if it was created? They cannot do much of anything "
         "without it."),
    ]),
    _s("account/access", "P3",
       ("teacher", "front office staff", "counselor", "librarian", "teaching aide", "coach", "registrar"), [
        ("Password reset emails not arriving",
         "I used the forgot password link twice and no email arrives, not even in junk. "
         "I can still work on the laptop I am logged in to, but my password expires Friday "
         "and I would rather not get locked out."),
        ("Self-service reset does not send the link",
         "The reset link never shows up. Tried with my school address and it just says "
         "'if the account exists an email was sent'. I will stop by the help desk later "
         "if that is easier."),
    ]),
    _s("account/access", "P3", ("teacher", "special education teacher"), [
        ("One student cannot get into the learning portal",
         "One student in my 3rd period class gets 'access denied' on the learning portal. "
         "Everyone else in the class is fine. He is working on a shared laptop with a "
         "partner for now, but that will not work for the quiz Thursday."),
        ("Student login not working, others are fine",
         "A student in room {room} can sign in to the laptop but not the portal. I had "
         "her try twice. Not sure if the problem is her account or the portal."),
    ]),
    _s("account/access", "P3",
       ("teacher", "front office staff", "counselor", "librarian", "registrar", "coach", "teaching aide"), [
        ("I keep getting signed out",
         "Since Monday I get signed out of everything every five or ten minutes and have to "
         "log back in. It is not a huge deal but it is really slowing me down."),
        ("Kicked out of my account every few minutes",
         "Something is wrong with my login. It logs me out while I am in the middle of "
         "typing and sometimes I lose the page. Other people near me do not seem to have "
         "this. It was fine last week."),
    ]),
    _s("account/access", "P3", ("office manager", "principal", "vice principal"), [
        ("Remove access for a former employee",
         "A staff member left at the end of last month but I noticed they still show in the "
         "shared drive permissions for the front office folder. Please remove them and check "
         "anything else they could still reach."),
        ("Resigned employee's accounts may still be active",
         "Following up on someone who resigned. HR sent the notice a few weeks ago. Their "
         "email still works as far as I can tell. Can you confirm everything has been "
         "turned off?"),
    ]),
    _s("account/access", "P4", ("vice principal", "office manager", "principal"), [
        ("Access request for incoming aide",
         "We have an aide starting in two weeks. Please set up an account and give them "
         "read access to the grade level shared folder and the supply request sheet. "
         "No rush, just do not want it forgotten."),
        ("Please add new aide to the shared folders and email list",
         "Request: add the new instructional aide to the team folder and the front office "
         "email list before they start on the 24th. Their school address can be anything "
         "standard. Thanks."),
    ]),
    _s("account/access", "P3", ("principal", "vice principal", "office manager"), [
        ("MFA codes not coming through",
         "When I sign in it asks for a verification code and nothing comes to my phone. I got "
         "a new phone last week, so I assume that is why. I can work from the one laptop "
         "that is already signed in, but I cannot add anything new or use my second "
         "computer."),
        ("Verification prompt never reaches my phone",
         "Trying to log in from home to finish the board report and the approval prompt does "
         "not show up. I use the school laptop at the building so I am not completely stuck, "
         "but I would like it fixed before I travel next week."),
    ]),

    # ------------------------------------------------------------------
    # hardware
    # ------------------------------------------------------------------
    _s("hardware", "P1", ("teacher", "vice principal", "counselor", "teaching aide"), [
        ("Laptop cart will not power on, testing starts soon",
         "The cart in room {room} will not charge or power anything. The light on the cart "
         "is off and none of the {n} laptops will turn on. State testing for this grade "
         "starts in 40 minutes and this is the only cart for the group."),
        ("Whole cart of student laptops dead before assessment",
         "We pulled the cart out for the assessment and not one laptop has any battery. Tried "
         "a different outlet. The whole grade is scheduled to test this morning. Please send "
         "someone now."),
    ]),
    _s("hardware", "P2", ("teacher", "special education teacher", "coach"), [
        ("Teacher laptop will not turn on",
         "My laptop will not power on at all this morning. Plugged in, held the button, "
         "nothing. All my lessons and the roster are on it and I have no spare. Can someone "
         "bring a loaner to room {room}?"),
        ("laptop dead, first period soon",
         "dead laptop. nothing on screen, no lights. i teach 1st period at 8:40"),
    ]),
    _s("hardware", "P2", ("front office staff", "office manager", "registrar"), [
        ("ID badge printer stopped working",
         "The badge printer at the front desk prints blank cards now. We have a field trip "
         "tomorrow and {n} visitor badges to print for chaperones. Cleaned it like the sheet "
         "says, no change. We do not have another one."),
        ("Badge printer out, need badges for tomorrow",
         "Our card printer gives an error light and will not feed. We need volunteer badges "
         "ready before tomorrow morning. Can someone look at it today?"),
    ]),
    _s("hardware", "P3", ("teacher", "special education teacher", "teaching aide"), [
        ("Projector flickering in room {room}",
         "The projector in room {room} flickers and sometimes goes dark for a few seconds. "
         "I have been using the whiteboard instead, which is fine for now, but the image "
         "is getting worse each day."),
        ("Classroom projector picture keeps cutting out",
         "Picture goes in and out about every ten minutes. Wiggling the cable helps a little. "
         "Not urgent, I have a workaround, but it is distracting for the kids."),
    ]),
    _s("hardware", "P4", ("front office staff", "registrar", "office manager", "counselor"), [
        ("Request for a second monitor",
         "Would it be possible to get a second monitor for my desk? I work in two systems all "
         "day and keep switching between tabs. Whenever you have spare equipment is fine."),
        ("Can I get an extra screen for my desk?",
         "I saw other offices have two screens. If there is one available, I would like to put "
         "in a request for one. Not urgent."),
    ]),
    _s("hardware", "P3", ("teacher", "teaching aide", "special education teacher", "counselor"), [
        ("Workroom printer jamming constantly",
         "The printer in the Building {bldg} workroom jams on nearly every job over a few "
         "pages. We have been using the one down the hall. Someone should look at the rollers "
         "before it gets worse."),
        ("Printer keeps eating paper",
         "paper jam every time again. cleared it three times today. the other printer works "
         "so we are ok but it is a pain"),
    ]),
    _s("hardware", "P4", ("teacher", "teaching aide", "special education teacher"), [
        ("Need a replacement keyboard and mouse",
         "Several keys on my keyboard are sticking and the mouse double clicks. Could I get "
         "a replacement set when you have one? Happy to drop the old ones off."),
        ("Headset request for intervention group",
         "I run a small reading group and we could use six headsets with a microphone. Not for "
         "this week, just whenever it works for your supply."),
    ]),
    _s("hardware", "P3", ("teacher", "teaching aide", "librarian", "vice principal"), [
        ("Student laptop screen cracked",
         "One of the classroom laptops has a cracked screen across the bottom third. It still "
         "works but the student cannot see the taskbar. We swapped to another one for today. "
         "Please advise whether to send it in."),
        ("Broken screen on a classroom laptop",
         "A student dropped a laptop off the desk. There is a crack in the corner and a dark "
         "patch spreading. We have enough spares this week."),
    ]),
    _s("hardware", "P3", ("front office staff", "registrar", "office manager", "counselor", "school nurse"), [
        ("Computer making a loud noise",
         "My desktop has been making a grinding or whirring sound since last week and it gets "
         "louder in the afternoon. It still works. I am just worried it is going to die in "
         "the middle of report cards."),
        ("Loud and slow computer, is it the fan?",
         "Not sure if this is a hardware thing or a software thing but my computer is loud and "
         "also slow lately. Is the fan something you handle?"),
    ]),
    _s("hardware", "P3", ("teacher", "special education teacher"), [
        ("Document camera not detected",
         "The document camera in room {room} stopped showing up on the display. The light on it "
         "is on. I can screen share from my laptop instead, but I rely on it for math "
         "examples."),
        ("Doc camera shows no picture",
         "doc camera gives a black screen now. tried another cable. the one in the room next "
         "door works fine so maybe it is the port?"),
    ]),

    # ------------------------------------------------------------------
    # software
    # ------------------------------------------------------------------
    _s("software", "P1", ("front office staff", "registrar", "office manager", "vice principal"), [
        ("Student information system is down",
         "The student information system has been showing an error page since 8:10. Nobody in "
         "the office can take attendance, and teachers are asking. The district report goes out "
         "at noon and it needs today's counts."),
        ("Attendance system will not load for anyone",
         "Cannot get into the attendance and records system, and neither can any teacher who "
         "has called me. It says the service is unavailable. This affects the whole building "
         "and we need to know whether to switch to paper."),
    ]),
    _s("software", "P2", ("teacher", "special education teacher", "coach"), [
        ("Gradebook app crashes on open",
         "The gradebook app closes by itself a second after I open it. I reinstalled it, same "
         "thing. Progress reports are due tomorrow morning and I have no other way to enter "
         "marks. It does open on a colleague's laptop, so I think it is my machine."),
        ("Gradebook closes right after it loads",
         "gradebook crashes every time. i have 90 minutes of prep and then 4 classes. need this "
         "working today for grade entry"),
    ]),
    _s("software", "P2", ("vice principal", "counselor", "teacher", "teaching aide"), [
        ("Assessment app will not start on half the test laptops",
         "We tested the assessment app on the cart for tomorrow and it fails to launch on about "
         "half of the laptops. It shows a spinning wheel and then closes. We need all {n} "
         "working for the morning session. Practice test is currently impossible."),
        ("Test software fails to launch before tomorrow's exam",
         "Ran the readiness check and the testing software will not start on {n} devices. The "
         "rest are fine. Please look at it today if you can, the exam is first thing tomorrow."),
    ]),
    _s("software", "P3", ("teacher", "teaching aide", "librarian"), [
        ("License expired message in the media lab",
         "Students in the media lab get a message that the license has expired when they open the "
         "video editing program. It lets them continue for 30 seconds then closes. We have been "
         "working in the older version on a few machines, but it is slow."),
        ("Editing software on lab computers needs activation",
         "Our editing software on the lab computers says it needs to be activated. A few "
         "students are using the web version for now. Not sure who handles licenses."),
    ]),
    _s("software", "P4", ("teacher", "teaching aide", "special education teacher"), [
        ("Install request: free graphing tool",
         "I would like a free graphing tool installed on the classroom laptops in room {room} "
         "for our functions unit. It runs in a browser or installs, whichever is easier. The "
         "unit starts in three weeks so there is no hurry."),
        ("Could a geometry program be added to the student laptops?",
         "Is it possible to get a simple geometry program added to the student laptops? The "
         "website is easy to find. Not needed until next month."),
    ]),
    _s("software", "P3", ("teacher", "special education teacher"), [
        ("Assignments page broken in one browser",
         "After the update over the weekend the assignments page shows a blank white area on "
         "the browser we normally use. If I open it in the other browser it is fine, so we are "
         "using that. Several teachers on my team see the same thing."),
        ("Learning site assignment list is empty",
         "The class website loads but the assignment list is empty. I know the assignments are "
         "there because students on their phones can see them. Might be a browser issue?"),
    ]),
    _s("software", "P4", ("teacher", "special education teacher"), [
        ("How do I share a document as view only?",
         "Quick question. I want to share a lesson document with the parents but make it so they "
         "cannot edit it. Is there a guide? I looked in the help folder and could not find it."),
        ("Training request for new reporting tool",
         "Is there a short training on the new reporting tool? Several of us on the team would "
         "like to learn it before the next marking period. Any time after school works."),
    ]),
    _s("software", "P3", ("registrar", "front office staff", "office manager", "counselor", "vice principal"), [
        ("Report export gives an empty file",
         "When I run the weekly attendance summary and click export, I get a file but there is "
         "nothing in it. Printing from the screen works, so I am doing it that way. It used to "
         "export fine."),
        ("The report will not export",
         "Report export is broken. I get a spreadsheet with just the heading row. Same result "
         "for the other two reports I tried."),
    ]),
    _s("software", "P2", ("principal", "vice principal"), [
        ("Email and calendar app stuck on loading",
         "The email and calendar app has been stuck on a loading screen for me since this "
         "morning. I have a meeting with parents at 1 and need to see who is coming. A "
         "restart did not help. I can only see messages in a browser on my phone, which is "
         "not enough for what I need to attach."),
        ("Mail app will not open",
         "Mail app will not open. Spinning circle forever. Closing and reopening does nothing. "
         "I have a call with the central office at 11 and need my files."),
    ]),

    # ------------------------------------------------------------------
    # network
    # ------------------------------------------------------------------
    _s("network", "P1", ("vice principal", "teacher", "counselor", "teaching aide"), [
        ("Wi-Fi down in all of Building {bldg}",
         "The Wi-Fi in Building {bldg} went out about 20 minutes ago. Every classroom is "
         "affected. We have {n} students in the middle of an online assessment and they have "
         "all been kicked off. Please treat as urgent."),
        ("No wireless anywhere in the building during testing",
         "Wireless is completely gone in the whole building. Laptops say connected but with "
         "no internet. Testing is happening right now and we are not sure what to tell the "
         "students or whether we have to restart the session."),
    ]),
    _s("network", "P1", ("principal", "office manager", "front office staff", "vice principal"), [
        ("Internet down at the east campus",
         "East campus has no internet since the start of the day. Wired and wireless both. "
         "The phones also seem to be out. We cannot reach anything online, including "
         "attendance. Is it a wider outage?"),
        ("Everything online is down on the east campus",
         "Everything online is down on the east campus. The office cannot get to email "
         "or the records system. A few teachers are using their phones as a hotspot but "
         "that cannot cover the whole building."),
    ]),
    _s("network", "P2", ("teacher", "special education teacher"), [
        ("Room {room} has no network at all",
         "Nothing connects in room {room}. The wired port is dead and the laptop cannot see the "
         "wireless. The rest of the hall is fine. I teach online curriculum all day and "
         "cannot do anything. I have moved to the library for now but my classes are stuck "
         "there too."),
        ("Classroom dead for wired and wireless",
         "Our classroom lost internet this morning. I tried the cable and Wi-Fi. Other "
         "rooms on the hall are working. Please send someone to room {room} today."),
    ]),
    _s("network", "P3", ("librarian", "teacher", "teaching aide"), [
        ("Wi-Fi very slow in the library",
         "From about 1:30 on the library Wi-Fi is painfully slow. Pages take a long time and "
         "videos buffer. In the morning it is fine. I assume it is when a lot of classes come "
         "in. A workaround is to use the wired computers."),
        ("Library internet crawling in the afternoons",
         "slow slow slow in the library. every day after lunch. students give up on research"),
    ]),
    _s("network", "P3", ("teacher", "special education teacher"), [
        ("Content filter blocking an educational site",
         "The filter blocks a science simulation site we use in class. It says 'category not "
         "allowed'. It is the standard site for the unit. I can show it from my own device on "
         "the projector so the lesson is not ruined, but students cannot use it themselves."),
        ("Video lesson blocked for students",
         "A video lesson from an educational channel shows as blocked on student laptops. It is "
         "fine on the staff network. Can it be allowed for students? The link is in the lesson "
         "plan folder."),
    ]),
    _s("network", "P4", ("teacher", "librarian", "special education teacher"), [
        ("Request to unblock a research site before April",
         "For our April unit I would like a particular history research site to be accessible "
         "to students. I have checked that it is school appropriate. Nothing needed right away."),
        ("Please allow a coding practice site before the next unit",
         "Can the filter be adjusted for a coding practice site? We start the unit in three weeks. "
         "I have the address if you want it. You can reach me at planning@example.org."),
    ]),
    _s("network", "P4", ("office manager", "principal", "vice principal"), [
        ("Network drop needed in new office",
         "The counseling office is moving to room {room} next month and will need a wired "
         "port near the back wall for a desktop. Can someone check what is in the room now?"),
        ("Request: add a second port at the new front desk",
         "Please add a network connection behind the new reception desk. There is only one "
         "port in the room and we need two. This is for the remodel, which is not finished "
         "until next quarter."),
    ]),
    _s("network", "P3", ("office manager", "registrar", "principal", "counselor"), [
        ("Cannot connect to VPN from home",
         "I cannot connect to the school VPN from home. It spins and then times out. I am "
         "using the same laptop and settings as last week. I can still get to my email in the "
         "browser, but not the shared records folder. I will be in the building on Thursday if "
         "it cannot wait."),
        ("VPN not working from home",
         "vpn is not connecting from home since yesterday afternoon. i can work around it for a "
         "day or two"),
    ]),
    _s("network", "P3", ("teacher", "front office staff", "office manager", "teaching aide"), [
        ("Internet is weird today",
         "The internet seems off today. Some pages load, some say 'cannot connect', and then "
         "five minutes later they work. Is something going on? I do not know if it is just "
         "where I am."),
        ("Sometimes it loads, sometimes not",
         "Everything online is hit and miss today. Email works, the records system is slow, and "
         "the lunch count page times out. It has not been totally down."),
    ]),
    _s("network", "P2", ("front office staff", "registrar", "office manager"), [
        ("Front office cannot reach the shared drive",
         "Nobody in the front office can open the shared drive. The folder shows an error about "
         "the network location not being available. We have the enrollment packets in there "
         "and families are waiting at the counter."),
        ("Shared files not opening for the office",
         "The office shared folder will not open on any of our computers. Internet works. "
         "We are missing the forms we need for today's registrations and have no copies."),
    ]),

    # ------------------------------------------------------------------
    # MDM/device
    # ------------------------------------------------------------------
    _s("MDM/device", "P1", ("vice principal", "teacher", "principal"), [
        ("Student laptops locked after overnight update",
         "This morning about {n} student laptops show a lock screen that says the device has "
         "been locked by an administrator. Staff laptops look fine. The students cannot get "
         "past it and a lot of them have no device for first period."),
        ("Devices say 'locked by administrator'",
         "Entire grade level cannot use their laptops. Black screen with a message about the "
         "device being managed and locked. It looks like something was pushed overnight. "
         "Several teachers have called the office."),
    ]),
    _s("MDM/device", "P2", ("teacher", "teaching aide", "counselor", "coach"), [
        ("New laptop will not enroll",
         "Got my replacement laptop this morning and it will not finish setup. It sticks on the "
         "enrollment screen and says it cannot contact the management server. I have no usable "
         "device otherwise, my old one is turned in already."),
        ("New laptop stuck on the enrollment step",
         "My new laptop has been stuck at the enrollment step for an hour. Retried with and "
         "without the network cable. I start with students in 30 minutes."),
    ]),
    _s("MDM/device", "P2", ("coach", "teacher"), [
        ("Lost a school tablet, please lock it",
         "I cannot find the tablet I use for roll. I last had it in the gym on Tuesday. "
         "It has the class lists on it. Please lock it or wipe it if you can, and tell me "
         "what to do next."),
        ("School tablet left on a bus after the trip",
         "Pretty sure my school tablet was left on a bus after the trip. It was signed in to "
         "email. Can you make sure nobody can use it?"),
    ]),
    _s("MDM/device", "P3", ("teacher", "counselor", "librarian", "teaching aide"), [
        ("Laptop stuck on old policy, apps will not install",
         "My laptop shows a banner that a policy is still applying, and has for days. A required "
         "app is not installing because of it. I can use a loaner laptop for the one tool I "
         "need, but I would like my own working."),
        ("New apps missing from my laptop's self-service list",
         "None of the new apps have shown up on this device and the self-service list is "
         "empty. Other laptops in my team got them. We can work around it by borrowing."),
    ]),
    _s("MDM/device", "P4", ("vice principal", "librarian", "office manager", "teacher"), [
        ("Add tablet cart to management before next term",
         "We are getting a cart of {n} tablets for the early grades next term. Could they be added "
         "to the management system and set up with the standard apps ahead of time? Boxes will "
         "be in the supply room."),
        ("Please enroll the new set of devices",
         "New devices arrived in Building {bldg}. Please enroll them and give them the same "
         "settings as the other cart. They will not be used until after the break."),
    ]),
    _s("MDM/device", "P3", ("teacher", "counselor", "librarian", "front office staff", "teaching aide", "registrar"), [
        ("Device shows not compliant warning",
         "My laptop says 'this device is not compliant' and some of the school sites no longer "
         "open. I can still reach the email through my phone. Not sure what I did."),
        ("Laptop flagged as non-compliant",
         "Got a message that the device is out of compliance and has to be fixed within 3 days. "
         "No explanation of what is wrong. I did not change any settings."),
    ]),
    _s("MDM/device", "P3", ("principal", "vice principal", "coach", "counselor"), [
        ("Work email gone after phone upgrade",
         "I upgraded my phone and my work profile is gone. I used to get email and the "
         "calendar on it. I can use the laptop and the browser for now, but I want the "
         "phone set up again so I get alerts."),
        ("How do I set up school email on my new phone?",
         "How do I put the school email on my new phone? I tried the link from the old guide "
         "and it says the device is not supported."),
    ]),
    _s("MDM/device", "P2", ("front office staff", "office manager"), [
        ("Front desk sign-in tablet stuck on setup screen",
         "After the power flicker the visitor sign-in tablet came back on a setup screen and "
         "will not go past it. We have no way to print visitor badges and we do not have a "
         "second one. Visitors are lined up for the assembly. We have a paper log for now, "
         "but the badges are what the district requires."),
        ("Visitor kiosk will not leave setup",
         "Kiosk at the front desk is stuck. It rebooted by itself and now only shows the "
         "first-time setup page. I cannot sign visitors in or print their stickers, and a "
         "group of volunteers just walked in. Please call the office line, not the cell."),
    ]),
    _s("MDM/device", "P4", ("teacher", "librarian", "counselor", "registrar"), [
        ("Why is my laptop managed?",
         "My laptop says it is managed by my organization and I cannot change the wallpaper or "
         "the sleep time. Is that normal? It is not stopping me from working, I just wondered "
         "whether I can get some of those settings back."),
        ("Cannot turn on dark mode",
         "I wanted to turn on dark mode and it is grayed out with a note that it is controlled "
         "by an administrator. Is there a way to allow it? Not urgent at all."),
    ]),

    # ------------------------------------------------------------------
    # other
    # ------------------------------------------------------------------
    _s("other", "P1", ("teacher", "special education teacher", "teaching aide"), [
        ("Burning smell from power strip in room {room}",
         "There is a burning plastic smell near the outlet behind my desk in room {room}. The "
         "power strip feels hot to the touch. I unplugged what I could and moved the students "
         "to the hallway. Someone needs to look at this immediately."),
        ("Hot power strip with a bad smell in a classroom",
         "A power strip with a projector and a charging cart is hot and smells bad. I turned "
         "the switch off. Calling this in because it is electrical and kids were near it."),
    ]),
    _s("other", "P1", ("custodian", "vice principal", "front office staff", "principal"), [
        ("Badge readers not unlocking exterior doors",
         "Badge readers on the exterior doors are not letting anyone in. Staff arriving are "
         "waiting outside. The doors stay locked unless someone opens them from the inside. "
         "We have a person at the front door but cannot do that for every entrance."),
        ("Badges will not open the side doors",
         "None of our badges open the side doors this morning. The light on the reader is "
         "red. About {n} staff are outside and the buses will arrive soon. Need this fixed "
         "or someone sent with a key."),
    ]),
    _s("other", "P2", ("front office staff", "office manager"), [
        ("Front office phones are dead",
         "All the phones in the front office have no dial tone. We cannot call out and "
         "parents cannot reach us. We are using a cell phone, which is not a long-term answer. "
         "The nurse and attendance calls are not getting through."),
        ("No dial tone in the main office",
         "office phones down since 9. nothing rings, nothing connects. the cell phone is the "
         "only thing we have"),
    ]),
    _s("other", "P3", ("teacher", "special education teacher", "teaching aide", "counselor"), [
        ("Hallway speakers very quiet",
         "The speakers in the hall by room {room} and the next few are barely audible. "
         "Announcements are missed. Other halls seem normal. It has been like that for "
         "about a week."),
        ("Intercom hard to hear in one hall",
         "I cannot hear the intercom in my area anymore. Others on the hall say the same. "
         "We have been relying on the office sending a runner for important messages."),
    ]),
    _s("other", "P4", ("teacher", "teaching aide", "special education teacher"), [
        ("When is the next training on the new gradebook?",
         "Is there a date for the next training on the new gradebook? I missed the session "
         "in August and would like to attend a make-up one when it is offered."),
        ("Training on classroom display tools?",
         "Do you run any trainings on the classroom display tools for new teachers? A few "
         "of us would join if it is after school."),
    ]),
    _s("other", "P4", ("teacher", "vice principal", "coach", "librarian"), [
        ("Sound and projector setup for the student showcase",
         "We are hosting a student showcase in the gym on the 19th. We will need a microphone "
         "setup and a projector with a screen. The sound check can happen the day before. "
         "Letting you know now so it can be scheduled."),
        ("Tech support for the evening concert",
         "For the evening concert next month can we get tech support in the auditorium "
         "from 5 pm? We also need a laptop connected to the big screen for the slideshow."),
    ]),
    _s("other", "P3", ("teacher", "office manager", "front office staff", "counselor", "registrar"), [
        ("Need a deleted folder recovered",
         "I deleted a folder of my files from the shared drive by mistake this morning. It is "
         "not in the trash. I have last week's copy on a flash drive so I am okay for "
         "now, but the newer version is lost. Can it be restored from a backup?"),
        ("Field trip forms folder missing from the office share",
         "Somebody removed the field trip forms folder from the office share. It was there "
         "on Friday. We can recreate the forms if we have to but it would take a long time."),
    ]),
    _s("other", "P2", ("principal", "vice principal", "counselor", "teacher"), [
        ("Auditorium setup for parent night tonight",
         "Parent night starts at 6 and the laptop in the auditorium will not show on the big "
         "screen. The wireless mic also crackles. I need someone to come and make it work "
         "before 5. We have no backup plan other than reading from paper."),
        ("Projector not picking up the podium laptop, event tonight",
         "Can someone meet me in the auditorium this afternoon? The projector input is "
         "not picking up the podium laptop and the event is tonight."),
    ]),
    _s("other", "P4", ("teacher", "coach", "school nurse", "librarian", "teaching aide"), [
        ("Question about using a personal tablet",
         "I would like to know the policy on connecting a personal tablet to the staff network. "
         "I would only use it for reading and attendance. If it is not allowed I will leave "
         "it at home."),
        ("Can personal phones be used for verification codes?",
         "Can staff use personal phones for the verification codes or is a school device "
         "required? I could not find this in the handbook."),
    ]),
    _s("other", "P3", ("teacher", "special education teacher", "teaching aide"), [
        ("Nothing works in room {room}",
         "Today in room {room} the projector will not turn on, the speakers hum, and the phone "
         "has no light. I do not know if it is a power thing or three separate problems. "
         "I am teaching without the display, which is annoying but possible."),
        ("everything in my room is acting up",
         "something is wrong in my classroom. several things stopped at once about "
         "the same time yesterday afternoon. not sure who to call so i am writing here"),
    ]),
)
