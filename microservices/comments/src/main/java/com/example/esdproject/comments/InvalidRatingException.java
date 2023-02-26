package com.example.esdproject.comments;

public class InvalidRatingException extends RuntimeException {
    InvalidRatingException() {
        super("Rating must be between 1-5 inclusive");
    }
}
