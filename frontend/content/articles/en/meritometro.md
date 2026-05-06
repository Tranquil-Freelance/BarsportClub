---
title: "The Arrest of the Scoreline: The ruthless truth of the Meritometro"
excerpt: "Three-nil is always three-nil. But the scoreline is perhaps the crudest, most unreliable measure of reality one can imagine in a complex sport like football. The Meritometro exists to tell the story that the scoreboard does not."
coverImage: "/images/home/meritometro-cover.webp"
date: "2026-04-03"
category: "Technical Analysis"
---

## The scoreboard lies

Three-nil. The game is over, the result is decisive, the table updates. The journalist writes that the winning team was superior, the losing coach comments that "the result is misleading," and everyone assumes he is making excuses.

But sometimes he is right.

The final score is a brutal tool of synthesis: it captures who scored more goals, not who played better. In a league where the average number of lucky shots (those that go in despite having a probability below 15%) is about two per matchweek across ten games, the number of results "distorted" by luck is structurally significant. It is not an anomaly — it is a feature of the game.

The Meritometro was born to make this distortion visible. Not to replace the result — football is a sport and results matter — but to accompany it with an alternative measure: who *deserved* to win, beyond how fortunate they were.

## The paradox of the result in modern football

Football is a low-scoring sport. This characteristic, which makes it dramatically compelling, also makes it statistically very noisy. In basketball, an average game sees 90-110 points per team; every additional quality possession translates almost certainly into points. In football, 1-3 goals are scored per match, and the variance of the result relative to the quality of play is enormously higher.

A study conducted over five seasons of Premier League showed that 34% of losses by high-quality teams (top 6) could be classified as "undeserved defeats" according to advanced metrics. Meaning: they had created more danger, controlled more of the game, had superior xG — and still lost.

This is not a scandal. It is the mathematics of football. But ignoring it means analyzing football through a defective lens.

## The architecture of IMR: what we really measure

The *Individual Match Rating* (IMR) is the computational heart of the Meritometro. It is a score that synthesizes the quality of a player's offensive and constructive contribution in a match, based exclusively on the metrics available in our database — derived from Understat, which collects advanced data on the Top 5 European leagues.

We do not measure tackles, interceptions, saves, or running distance: not because these data do not exist, but because they fall outside the perimeter of our primary source. What we measure, we measure well.

### xG — Expected Goals

xG is the starting point of everything. For every shot on goal, the model estimates the probability that it will become a goal, based on field position, angle, type of assist received, and game situation. A shot from a central position a few meters from goal will have high xG; one from outside the box with a difficult angle will have low xG.

The value of xG for the Meritometro is that it decouples evaluation from outcome: a striker who accumulates 1.8 xG in a match is doing excellent work, regardless of whether they scored or not. Conversely, a striker who scores from a midfield shot with an xG of 0.04 was lucky — and the IMR knows it.

### xA — Expected Assists

xA measures the quality of the pass leading to the shot, not whether the shot goes in. An assist on a perfect cross that the striker sends over the bar is a missed assist in traditional statistics; in xA it is still a high-quality contribution, because it generated a dangerous situation.

This is especially important for reevaluating creative midfielders, who often do not appear in traditional assist rankings despite having generated dozens of high-quality opportunities over the course of a season.

### xGChain — Involvement in the entire action

xGChain is the most undervalued metric and, in some ways, the most revolutionary. It measures a player's involvement in any action that leads to a shot: not just the final pass (the one that generates the assist), but all touches in the preceding chain.

A trequartista who receives the ball, releases it quickly, makes a run, receives the return pass, and then distributes for the shot: traditional assist models might attribute nothing to them. xGChain captures their contribution to the entire sequence. It is the metric that answers the question: "how dangerous would this team be if we removed this player from their actions?"

### xGBuildup — Construction in the early phases

xGBuildup is similar to xGChain, but focuses on the buildup phases farther from the opponent's goal. It measures contribution to dangerous actions in their initial phase: the defender who builds from the back, the holding midfielder who distributes vertically, the trequartista who drops deep to receive and turn.

This metric is essential for evaluating players who work in areas of the pitch where traditional offensive statistics do not reach. A quality deep-lying playmaker who never appears among the scorers or assist providers, but who has high xGBuildup, is a player who makes the machine run — and the Meritometro sees it.

### PPDA and Deep Completions — Team-level dominance

At the individual level, the IMR is built on the metrics described above. But the context in which a player operates is important: that is why we use two team metrics to normalize individual contributions.

The **PPDA** (Passes per Defensive Action) measures how many passes a team allows its opponents before making a defensive intervention. A low PPDA indicates a team that presses high and wins the ball back quickly — a favorable context for those playing forward. **Deep Completions** count passes completed in the advanced areas of the opponent's half: an indicator of the ability to penetrate and create danger in decisive zones.

These two indicators allow us to understand how much a player is expressing their values in a system that amplifies or compresses them — and to adjust the weight of individual contributions accordingly.

## How the Meritometro dismantles "luck"

"Luck" in football is not random in the strict sense. It is a statistical residual: the difference between what the game produced in terms of quality and what the scoreline recorded. The Meritometro seeks to isolate this residual.

A concrete example. On a matchday in Serie A, a mid-table team beats the league leaders 1-0 with a shot from outside the box five minutes from time (goal probability: 6%). The leaders had generated 2.4 xG against 0.3 xG. The scoreboard says victory; the IMR says the collective merit was on the other side.

Over the long term — thirty to forty games — these residuals balance out. But in the short term, a sequence of unlucky results can degrade the public perception of a player or a team in a completely unjustified manner. The Meritometro records this alternative reality.

It is not about rewriting history. It is about understanding what lies beneath.

## IMR standings vs. traditional standings: emblematic cases

One of the most revealing comparisons the Meritometro produces is the season-long ranking based on cumulative average IMR against the actual points table.

Systematically, two categories of anomalous teams emerge.

**"Over-performing" teams** are those that collect more points than their IMR would suggest. Typically they have an exceptional goalkeeper (who turns opponents' xG into nothing), a striker above average in finishing efficiency, or both. Detached from their luck, they often regress the following season.

**"Under-performing" teams** collect fewer points than they deserve. These are the most interesting: often teams with high-quality play that suffer from a particularly adverse distribution of luck. Historically, these teams tend to improve the following season without needing market interventions, simply because luck normalizes.

This information has enormous practical value — not merely academic. A sporting director who buys a striker from an "over-performing" team might be paying based on results that will not repeat. One who sells a defender from an "under-performing" team might be getting rid of a key element at the worst possible moment.

## Who really deserves it?

The most uncomfortable question the Meritometro poses is this: does the player who wins the MVP award for the season really deserve it, or were they simply luckier than the others?

The answer, in the majority of cases, is that the award is *largely* justified — top players have high IMR because they generate real quality, not because they are lucky. But there are significant exceptions. In our database of the last ten seasons of the major European leagues, we have identified twenty-three cases where the league's top scorer had an IMR in the mid-range of their league — that is, a player who scored many goals but contributed relatively little to the game in its totality.

Twenty-three top scorers who were, statistically, average players in overall quality. This does not diminish their scoring ability, which is real. But it says that scoring is one part of football, not the whole of football.

## The Meritometro as a tool of fairness

Ultimately, the Meritometro is a tool of fairness. It seeks to give each player what they are due, net of bad luck, refereeing errors, goalkeepers having the game of their lives, woodwork, and millimeters.

It is not infallible. No metrics system is. There are aspects of football that numbers do not capture well: defensive leadership in crisis situations, the charisma that lifts teammates in a difficult moment, the ability to change the psychological momentum of a game. These things exist and matter. The Meritometro does not see them — or sees them only indirectly, through the effects they produce on others' numbers.

But what the Meritometro sees, it sees well. And it sees systematically, without prejudice, without preferred nationalities, without big names distorting judgment. It is ruthless in the way only numbers can be ruthless: without rancor, without bias, with the sole ambition of telling reality as it was — not as we would have liked it to be.

The scoreboard says three-nil. The Meritometro says who deserved it.
