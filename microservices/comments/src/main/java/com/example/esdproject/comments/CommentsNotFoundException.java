package com.example.esdproject.comments;

public class CommentsNotFoundException extends RuntimeException {
    CommentsNotFoundException(Integer id) {
        super("Could not find comment " + id);
    }
}
