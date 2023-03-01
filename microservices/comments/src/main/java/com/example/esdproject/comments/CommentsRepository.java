package com.example.esdproject.comments;

import org.springframework.data.repository.CrudRepository;
import java.util.Optional;

public interface CommentsRepository extends CrudRepository<Comments, Integer> {
    Optional<Comments> findByGroomerId(Integer groomerId);
}
