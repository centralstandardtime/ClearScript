// Fibonacci sequence calculator
int n = 10;
int fib1 = 0;
int fib2 = 1;
int current = 0;
int count = 0;

function fibonacci() {
    while (count < n) {
        current = fib1 + fib2;
        fib1 = fib2;
        fib2 = current;
        count++;
    }
}

label: start
    fibonacci();
    kill();
