Implement a Tactical Recruitment Engine within FM Parser.

Goal

Instead of filtering players by individual attributes, rank every player based on how well they fit a tactical profile.

Requirements

Create YAML tactical profiles for each position.

Each profile must support:

- Position
- Role
- Description

Attribute groups

Essential
Important
Useful
Bonus

Each attribute has a weighting.

Example

weights:
  Anticipation: 30
  Pace: 25
  Decisions: 20
  Positioning: 15
  Passing: 10

Minimum acceptable values

minimums:
  Pace: 11
  Anticipation: 11

Preferred values

preferred:
  Passing: 11
  Composure: 11

Physical profile

Mental profile

Technical profile

Preferred personalities

Preferred traits

Traits to avoid

Age profile

Hidden attribute preferences

Budget profile

League scaling

Allow minimum values to be overridden per division.

Example

National League

Pace 11
Anticipation 11

League Two

Pace 12
Anticipation 12

Championship

Pace 13
Anticipation 13

Scoring

Calculate:

Overall Tactical Fit (%)

Category scores

Technical
Mental
Physical
Personality

Recommendation

A+
A
B
C
D
F

Recommendation text

Sign Immediately
Sign if Price is Right
Squad Player
Loan Only
Avoid

Comparison

Compare every candidate against the current player occupying that squad role.

Display

Current Player

Pace +2

Anticipation -1

Passing +3

Overall Upgrade

Yes / No

Filtering

Support

Maximum transfer fee

Maximum wage

Interested in joining

Work permit eligibility

Contract expiry

Output

Produce ranked recruitment reports and shortlist recommendations.