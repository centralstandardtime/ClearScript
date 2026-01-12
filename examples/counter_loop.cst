// Counter and loop demonstration
int counter = 0;
int limit = 10;
int step = 2;

function incrementCounter() {
    counter = counter + step;
}

function resetCounter() {
    counter = 0;
}

label: countLoop
    incrementCounter();
    
    if (counter >= limit) {
        goto resetAndEnd;
    }
    
    wait(1);
    goto countLoop;

label: resetAndEnd
    resetCounter();
    kill();
