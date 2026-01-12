// Advanced mathematical operations
// Demonstrates function calls and floating point math

float angle = 0.0;
float sineValue = 0.0;
float cosineValue = 0.0;
int iterations = 0;

function calculateSine(x) {
    // Using Taylor series approximation for sine
    // sin(x) ≈ x - x³/6 + x⁵/120
    float x2 = x * x;
    float x3 = x2 * x;
    float x5 = x3 * x2;
    
    sineValue = x - (x3 / 6.0) + (x5 / 120.0);
}

function calculateCosine(x) {
    // Using Taylor series for cosine
    // cos(x) ≈ 1 - x²/2 + x⁴/24
    float x2 = x * x;
    float x4 = x2 * x2;
    
    cosineValue = 1.0 - (x2 / 2.0) + (x4 / 24.0);
}

label: mathLoop
    calculateSine(angle);
    calculateCosine(angle);
    
    angle = angle + 0.1;
    iterations++;
    
    if (iterations < 10) {
        wait(1);
        goto mathLoop;
    }

    kill();
