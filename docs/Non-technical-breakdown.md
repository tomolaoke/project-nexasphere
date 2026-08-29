# NexaSphere, Explained Simply

No jargon. If you've never written a line of code, this page is for you.

## The problem, in one picture

Imagine a shop owner who checks their sales at the end of the month and
sees revenue went up. Great news, right? But when they actually count the
profit, it barely moved. Somewhere between "sold more stuff" and "kept more
money," something went wrong — maybe they gave too many discounts, maybe
too many items got returned, maybe deliveries kept failing and customers
stopped trusting the brand.

Finding out *which one* normally means opening five different notebooks —
one for sales, one for returns, one for deliveries, one for stock, one for
marketing — and trying to connect the dots by hand. That takes time, and
it's easy to miss something.

## What we built

A tool that does that dot-connecting automatically. You open one screen and
it immediately tells you things like:

> "Your revenue went up 63%, but your profit only went up 54%. That gap is
> worth looking into."

> "Your Audio products are being returned way more than everything else —
> mostly because customers say the product 'wasn't as expected.'"

> "One of your delivery companies is late 34% of the time, while your other
> delivery companies are only late about 8% of the time."

You can also just type a question, like "which marketing campaign gave us
the best return?" and get a straight answer.

## Why this needed AI at all

Couldn't a spreadsheet do this? A spreadsheet can show you numbers, but it
can't explain them in plain sentences, and it definitely can't say "here's
why this matters and here's what to check next." That's the part AI is good
at: turning numbers into a story a busy person can act on in ten seconds.

## The most important promise we made to ourselves

A lot of "AI does your business analysis" tools quietly let the AI make up
numbers that sound believable but are wrong. We refused to build it that
way. In our system, **a plain calculator (not the AI) does every single
number**, and the AI is only ever allowed to explain a number that the
calculator already produced. If the AI ever tries to say a number that
isn't real, our system catches it and throws that sentence away, replacing
it with a safe, pre-written one instead. You can trust every figure on the
screen.

## Why we built it this way, and not simpler

We could have just wired an AI chatbot straight to a spreadsheet and let it
answer freely. That's what most similar tools do, and it's genuinely risky
— the AI can get the math wrong while sounding completely confident. We
built the boring, careful version instead: the numbers come from real
calculations, checked against a separate "known-correct" answer key while we
were building it, and the AI's job is strictly limited to putting those
numbers into a sentence a manager can read in five seconds.

## Who this is for

Any manager at a growing business — retail, online store, logistics
company, whatever — who has data sitting in spreadsheets but doesn't have a
data analyst sitting next to them to make sense of it every day.
