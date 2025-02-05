## Functional Requirements

The business requires an easy to use application that will assist English students with learning the French language.

Safeguards must be in place to ensure that unsuitable language is not processed or returned to the student.

Ideally a local solution will be possible so that on-going costs are limited and do not require the purchase of cloud computing power.

The application will track each students progress and output encouraging messages for milestones such as practiced 50 words.

## Assumptions

The application will have a low number of concurrent users and a local PC/Laptop will be sufficent for the initial proof of concept.

An open source LLM will be preferred in order to reduce costs.  Due to hardware limitations, the initial proof of concept will use the smallest possible parameter size LLM that gives acceptable results.  Caching may be added at a later stage to improve response times.

## Data Strategy

A small database will be used to store the language training materials and it is expected that this will be less than 10G in size.  Vector embeddings will be used as part of sentence generation to allow the student to practice using words with similar semantic meaning.
