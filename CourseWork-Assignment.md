# Coursework Assignment
WeSalon is a brand-new mode for Online to Offline academic discussions. 

With the help of this tool, students can publish the discussion activity online and communicate
with academic partners offline. 

Specifically, a student can apply for an activity at a certain place, list all the activities,
participate in an activity and make some comments on a held activity.
 
You are required to design a corresponding database to support the normal operations of the WeSalon
system.

## Assumptions
- There are three status of the activities, which are reserved,ongoing, finished.

- Each activity must be held in a certain place over a period of time. 
Therefore, activities cannot be overlapped.

## Tasks
Design a database for the WeSalon system that allows students to
1. Manage the activities;
2. Update (modify/delete) the status of the activities.
3. Display each status of the activities separately.

4. Apply for an activity;(each activity has its own capacity, please note the possible conflicts with previously reserved places or time)

5. Participate in an activity; (a student can participate in an activity if there are no
conflicts with other participated activities and the current participation number is
below the activity capacity)

6. Comment on an activity; (a student can only comment on an activity iff he/she
has participated in the activity and the activity has been finished)

7. Filter the activities. (e.g. sort the reserved activities that will hold English Corner
ascending by the start time and descending by the activity capacities. You can filter
any type of activities as you like)

8. Code a demo programme to implement the system
9. You can use any language for programming, and any kind of GUI
is acceptable.