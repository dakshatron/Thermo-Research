Here's the problem statement:
- the NIST Reaction Kinetics database has a treasure trove of data on how quickly many different reactions progress
- a new extremely high quality dataset on reaction pathways of organic reactions has 30K+ reaction mechanisms/steps broken down by hand by chemists, in standardized (canonical SMILES) formats, specifying exactly which bonds are broken/formed, assigning IDs for you to follow a single atom through a reaction

I'm trying to leverage both to predict a given reaction's Arrhenius rate constant equation parameters (k = A * exp(- E_a/RT, I'm predicting A and E_a, the pre-exponential factor and activation energy, respectively) by:
- decomposing any given reaction into the likely mechanisms/steps in between
- homing in on the specific atoms most likely to speed up, or slow down, a reaction
- getting an idea of how fast or slow certain mechanisms are.

The database and publication links are here:
- https://kinetics.nist.gov/kinetics/
- https://www.nature.com/articles/s41597-024-03709-y


In /Web Scraping, you can find my pandas/regex programs that I used to scrape:
- the NIST Reaction Kinetics database, found here: 
- working on extracting SMILES from cactus.nih.gov/
- working on extracting SMILES from pubchem.gov/ using Selenium to automate scraping dynamic/Java based webpages

In /Data Cleaning & Transformation, you can find my pandas programs I'm working on to convert the NIST reactions in countless formats to either:
- useable bit vectors (Morgan fingerprints, or MACCS) for traditional machine learning using scikit learn and a new scikit-fingerprints library for chemoinformatics, more info here: chrome-extension://efaidnbmnnnibpcajpcglclefindmkaj/https://arxiv.org/pdf/2407.13291
  
- canonical SMILES strings, parsable by an LM (ain't got the dough for the second L there lol) transformer (bi directional long short term memory might be the best architecture here) to help encode the reaction characteristics and steps (likely bonds broken/formed, etc.), for deep learning with PyTorch; it seems more likely by the day this path will be overkill and maybe even counterproductive though
  

I'm still playing with the pathways dataset to see how I can make the chemical fingerprint datatypes work how I want, and cleaning up the data.
