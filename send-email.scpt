tell application "Mail"
    set theMessage to make new outgoing message with properties {subject:"DAX Workout Timer - AI Form Tracking Web App", content:"Hi,

I built a workout timer web app with AI form tracking for DAX (the personal trainer agent).

GitHub Repo: https://github.com/waterbourne/dax-workout-timer

Features:
- Simple Mode: Clean workout timer
- AI + Camera Mode: TensorFlow.js pose detection for rep counting and form feedback
- Works on phone and desktop
- Auto-imports workouts from JSON file
- Sound + vibration alerts

The AI mode uses MoveNet to detect squats and push-ups, counts reps automatically, and gives form feedback.

To use:
1. Clone the repo
2. Run: python3 -m http.server 8000
3. Open: http://localhost:8000/dax-workout-timer.html

Best,"}
    
    tell theMessage
        make new to recipient at end of to recipients with properties {address:"tars.agent@7islands.io"}
        make new cc recipient at end of cc recipients with properties {address:"adityabhavnani@gmail.com"}
        make new cc recipient at end of cc recipients with properties {address:"harish.hoon@gmail.com"}
        send
    end tell
end tell
