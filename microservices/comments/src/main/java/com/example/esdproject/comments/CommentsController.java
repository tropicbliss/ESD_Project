package com.example.esdproject.comments;

import org.springframework.web.bind.annotation.*;

@RestController
public class CommentsController {
    private CommentsRepository commentsRepository;

    public CommentsController(CommentsRepository commentsRepository) {
        this.commentsRepository = commentsRepository;
    }

    @PostMapping("/")
    public Comments createComment(@RequestBody Comments comment) {
        if (comment.getRating() < 1 || comment.getRating() > 5) {
            throw new InvalidRatingException();
        }
        return commentsRepository.save(comment);
    }

    @GetMapping("/{id}")
    public Comments getComment(@PathVariable Integer id) {
        return commentsRepository.findByGroomerId(id).orElseThrow(() -> new CommentsNotFoundException(id));
    }
}
