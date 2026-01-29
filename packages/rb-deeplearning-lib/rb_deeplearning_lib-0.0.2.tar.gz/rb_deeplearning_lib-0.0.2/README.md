# Deeplearning Package

## Overview

This package is designed to be similar to the PyTorch system of a building block system. Providing the functions that can be mixed, matched, and customized as pleased for any given model. This library is bare bones and only includes the few methods and ideas I learned about while studying *Deep Learning* by Ian Goodfellow et. al.. AI was used in the project, but it was used sparingly.

## Modules

This project has three main modules:

* `autogradient.py`  
* `sequence.py`  
* `neural_net.py`

All of which are automatically part of the initial import of the package.

## Making and Running a Model

When creating a model, use the Model class, which runs most of the functions included in the package itself. The first argument is a list of layers or blocks, each element is the steps in the network. These steps can be a Dense, Layer, or Dropout blocks (more will be made), a Dense is just multiple layers stacked back to back.   
Training a model is done through: def train(epochs, x\_t, y\_t, x\_v, y\_v, val\_run=1, l\_rate=0.01, \_lambda\=0.1, batch\_size \= None)  
Where epochs is the number of times you train through the data, the \#\_t means training data and \#\_v means validation data, x means input, y means output, val\_run is the epochs between when you want to test the validation data, l\_rate is the learn rate, \_lambda is a hyperparameter that determines the strength of the penalty functions, and batch\_size determines how large batches will be (if the batch size isn’t a multiple of the data size then it will still run, there is just a smaller batch then the others). 

## Dependencies

The auto gradient–which is used for back propagation–relies heavily on **numpy**.
