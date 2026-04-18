
# Logarithms

## The core idea

Multiplication lets you add a number to itself repeatedly. Exponentiation lets you multiply a number by itself repeatedly:

    2 × 2 × 2 = 2³ = 8

A logarithm asks the question **in reverse**: how many times must I multiply 2 by itself to get 8?

    log₂(8) = 3

That's it. A logarithm is just the **inverse of exponentiation**, the same way subtraction is the inverse of addition and division is the inverse of multiplication.

## The three parts

Every logarithm has three components. They are the same three numbers that appear in an exponentiation, just rearranged:

| Exponent form | Logarithm form | In words |
|---|---|---|
| 2³ = 8 | log₂(8) = 3 | "2 raised to **what power** gives 8? Answer: 3" |
| 10² = 100 | log₁₀(100) = 2 | "10 raised to **what power** gives 100? Answer: 2" |
| 5¹ = 5 | log₅(5) = 1 | "5 raised to **what power** gives 5? Answer: 1" |
| 7⁰ = 1 | log₇(1) = 0 | "7 raised to **what power** gives 1? Answer: 0" |

The small subscript number (2, 10, 5, 7 above) is called the **base**. The number inside the parentheses is called the **argument**. The result is called the **exponent** or **logarithm**.

General rule:

    If   bˣ = y
    then logb(y) = x

## Building intuition with base 10

Base 10 is the friendliest starting point because we use a decimal number system.

| log₁₀(x) | x | Why |
|---|---|---|
| 0 | 1 | 10⁰ = 1 |
| 1 | 10 | 10¹ = 10 |
| 2 | 100 | 10² = 100 |
| 3 | 1,000 | 10³ = 1,000 |
| 4 | 10,000 | 10⁴ = 10,000 |
| 6 | 1,000,000 | 10⁶ = 1,000,000 |

Notice the pattern: log₁₀ counts **how many digits minus one** the number has (for exact powers of 10). A million has 7 digits, so log₁₀(1,000,000) = 6.

For numbers between powers of 10, the logarithm is a decimal:

    log₁₀(50) ≈ 1.699

This makes sense — 50 is between 10¹ = 10 and 10² = 100, so its log is between 1 and 2.

## What about non-integer logarithms?

When the answer isn't a whole number, the logarithm still works the same way:

    log₂(6) ≈ 2.585

This means 2^2.585 ≈ 6. You can verify: 2² = 4 (too small), 2³ = 8 (too big), so the answer is between 2 and 3.

Fractional exponents are real — 2^2.5 means 2² × 2^0.5 = 4 × √2 ≈ 5.66. The math is consistent, even when the numbers stop being neat.

## Common bases

| Name | Notation | Base | Where you see it |
|---|---|---|---|
| Common logarithm | log(x) or log₁₀(x) | 10 | Sciences, engineering, decibels, pH scale, Richter scale |
| Binary logarithm | log₂(x) or lb(x) | 2 | Computer science, information theory, algorithm analysis |
| Natural logarithm | ln(x) or logₑ(x) | e ≈ 2.718 | Calculus, physics, compound growth, statistics |

The base doesn't change what a logarithm *is* — it just changes which multiplication you're counting.

## The key rules

There are a handful of rules that make logarithms powerful. Each one follows directly from how exponents work.

### Product rule

    logb(x × y) = logb(x) + logb(y)

Multiplying inside the log becomes addition outside. This is because exponents add when you multiply: b^m × b^n = b^(m+n).

**Example:** log₂(4 × 8) = log₂(4) + log₂(8) = 2 + 3 = 5. Check: 4 × 8 = 32 = 2⁵. ✓

### Quotient rule

    logb(x / y) = logb(x) − logb(y)

Dividing inside the log becomes subtraction outside.

**Example:** log₁₀(1000 / 10) = log₁₀(1000) − log₁₀(10) = 3 − 1 = 2. Check: 1000 / 10 = 100 = 10². ✓

### Power rule

    logb(xⁿ) = n × logb(x)

An exponent inside the log gets pulled out as a multiplier.

**Example:** log₂(8²) = 2 × log₂(8) = 2 × 3 = 6. Check: 8² = 64 = 2⁶. ✓

### Change of base

    logb(x) = logc(x) / logc(b)

You can convert between any two bases by dividing. This is why calculators only need one log button — you can derive the rest.

**Example:** log₂(8) = log₁₀(8) / log₁₀(2) ≈ 0.903 / 0.301 = 3. ✓

## Why logarithms matter

### They tame large numbers

Logarithms compress huge ranges into manageable ones. This is why many real-world scales are logarithmic:

- **Richter scale**: An earthquake of magnitude 6 is 10× more powerful than magnitude 5 (each step is ×10)
- **Decibels**: 80 dB is 10× the sound intensity of 70 dB
- **pH**: A pH of 3 is 10× more acidic than pH 4

### They describe "how many times can you halve something?"

log₂(n) answers: how many times can you cut n in half before you reach 1?

    log₂(1024) = 10

Start with 1024 → 512 → 256 → 128 → 64 → 32 → 16 → 8 → 4 → 2 → 1. That's 10 halvings.

This is why binary search runs in O(log n) time — each step eliminates half the remaining items.

### They show up in growth and decay

Any process where the *rate* of change is proportional to the *current amount* — population growth, radioactive decay, compound interest — is described by exponentials. Logarithms let you solve for the time variable:

    If a population doubles every year: P = P₀ × 2ᵗ
    How long to reach 1,000,000 from 1,000?

    2ᵗ = 1,000,000 / 1,000 = 1,000
    t = log₂(1,000) ≈ 9.97 years

## Common pitfalls

**You cannot log a negative number or zero.** Since bˣ is always positive (for positive b), there's no exponent that makes b^x = 0 or b^x = −5. The logarithm is undefined for those inputs.

**log(x + y) ≠ log(x) + log(y).** The product rule applies to multiplication, not addition. There is no clean simplification for the log of a sum.

**log(x) is not the same as ln(x)** unless context makes it clear. In mathematics, "log" often means natural log (base e). In computer science and engineering, "log" often means base 2 or base 10. Always check the convention.

## Quick reference

    logb(1) = 0              (any base raised to 0 is 1)
    logb(b) = 1              (any base raised to 1 is itself)
    logb(bⁿ) = n             (definition)
    b^(logb(x)) = x          (definition, the other direction)
    logb(x × y) = logb(x) + logb(y)
    logb(x / y) = logb(x) − logb(y)
    logb(xⁿ) = n × logb(x)
    logb(x) = logc(x) / logc(b)
