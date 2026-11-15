# Notes from the HBS ETA Conference 2026

Five articles from the 12th Annual Harvard Business School Entrepreneurship Through Acquisition Conference (14 November 2026), written for people searching for a small business to buy and wondering how to pay for it.

**Read it here:** https://wilsonwu-ai.github.io/hbs-eta-2026/

By Wilson Wu, founder of Dubbs Capital: an operator searching for a small business to buy.

## The story in three parts

- **Situation.** Luke Tatone, the founder of Searchfunder, invited me to the conference.
- **Task and action.** Attend as many sessions as I could and learn from people who have done it: Mitt Romney's opening fireside chat, the lenders' panel on the new SBA rules, Jordan Dubin's Guild Garage keynote and the roll-ups panel.
- **Result.** One overview and four session articles, each with plain-language boxes, diagrams, animated figures, and a 90-second explainer video on the new SBA rules and the capital stack.

## How it was checked

- Speaker remarks are paraphrased and attributed, never quoted.
- Outside facts (bios, dates, company facts, SBA rules) link to a source listed at the bottom of each page.
- Every capital stack and dollar example is illustrative, not a real deal. Confirm SBA rules with your lender.

## Rebuild

```bash
pip install markdown
python3 build.py      # content/*.md + templates/figures/*.html -> docs/*.html
python3 -m http.server --directory docs 8000
```

The video source is in `motion/` (HyperFrames compositions and the narration script).

Educational only. Not investment, legal or tax advice. Not affiliated with or endorsed by Harvard Business School or the HBS ETA Club.
