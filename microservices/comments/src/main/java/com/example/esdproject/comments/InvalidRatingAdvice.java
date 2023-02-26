package com.example.esdproject.comments;

import org.springframework.http.HttpStatus;
import org.springframework.web.bind.annotation.ControllerAdvice;
import org.springframework.web.bind.annotation.ExceptionHandler;
import org.springframework.web.bind.annotation.ResponseBody;
import org.springframework.web.bind.annotation.ResponseStatus;

@ControllerAdvice
public class InvalidRatingAdvice {
    @ResponseBody
    @ExceptionHandler(InvalidRatingException.class)
    @ResponseStatus(HttpStatus.BAD_REQUEST)
    String invalidRatingHandler(InvalidRatingException ex) {
        return ex.getMessage();
    }
}
