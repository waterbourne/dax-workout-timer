#!/usr/bin/env node
/**
 * Dax Workout Delivery Helper
 * Writes workout to JSON file for auto-import into web app
 */

const fs = require('fs');
const path = require('path');

const WORKOUTS_FILE = path.join(__dirname, 'dax-workouts.json');
const MAX_WORKOUTS = 6;

function parseWorkoutFromArgs() {
    const args = process.argv.slice(2);
    if (args.length < 3) {
        console.error('Usage: node dax-deliver.js "Title" "Focus" "exercise1|30|detail,exercise2|45|detail..."');
        process.exit(1);
    }
    
    const [title, focus, exercisesStr] = args;
    const exercises = exercisesStr.split(',').map(e => {
        const [name, duration, detail] = e.split('|');
        return {
            name: name.trim(),
            duration: parseInt(duration) || 30,
            detail: detail || '',
            type: 'main',
            phase: 'WORK'
        };
    });
    
    return {
        id: 'dax_' + Date.now(),
        date: new Date().toLocaleDateString('en-US', { 
            weekday: 'short', 
            month: 'short', 
            day: 'numeric',
            hour: 'numeric',
            minute: '2-digit'
        }),
        title,
        focus,
        exercises,
        source: 'dax_cron'
    };
}

function loadWorkouts() {
    try {
        const data = fs.readFileSync(WORKOUTS_FILE, 'utf8');
        return JSON.parse(data);
    } catch (e) {
        return { version: '1.0', lastUpdated: '', workouts: [] };
    }
}

function saveWorkouts(data) {
    data.lastUpdated = new Date().toISOString();
    fs.writeFileSync(WORKOUTS_FILE, JSON.stringify(data, null, 2));
}

function addWorkout(workout) {
    const data = loadWorkouts();
    
    // Check if already exists
    if (data.workouts.find(w => w.id === workout.id)) {
        console.log('Workout already exists, skipping');
        return;
    }
    
    // Add to front
    data.workouts.unshift(workout);
    
    // Keep only max
    if (data.workouts.length > MAX_WORKOUTS) {
        data.workouts = data.workouts.slice(0, MAX_WORKOUTS);
    }
    
    saveWorkouts(data);
    console.log(`✓ Workout added: ${workout.title} (${workout.exercises.length} exercises)`);
}

// Main
const workout = parseWorkoutFromArgs();
addWorkout(workout);
