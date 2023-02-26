package com.example.esdproject.comments;

import jakarta.persistence.*;

import java.util.Objects;

@Entity
public class Comments {
    @Id
    @GeneratedValue(strategy = GenerationType.AUTO)
    private Integer id;
    @Column(nullable = false)
    private Integer groomerId;
    @Column(nullable = false)
    private Integer userId;
    @Column(nullable = false)
    private String title;
    @Column(nullable = false)
    private String message;
    @Column(nullable = false)
    private Integer rating;

    public Integer getId() {
        return id;
    }

    public void setId(Integer id) {
        this.id = id;
    }

    public Integer getGroomerId() {
        return groomerId;
    }

    public void setGroomerId(Integer groomerId) {
        this.groomerId = groomerId;
    }

    public Integer getUserId() {
        return userId;
    }

    public void setUserId(Integer userId) {
        this.userId = userId;
    }

    public String getTitle() {
        return title;
    }

    public void setTitle(String title) {
        this.title = title;
    }

    public String getMessage() {
        return message;
    }

    public void setMessage(String message) {
        this.message = message;
    }

    public Integer getRating() {
        return rating;
    }

    public void setRating(Integer rating) {
        this.rating = rating;
    }

    @Override
    public boolean equals(Object o) {
        if (this == o) return true;
        if (o == null || getClass() != o.getClass()) return false;
        Comments comments = (Comments) o;
        return id.equals(comments.id);
    }

    @Override
    public int hashCode() {
        return Objects.hash(id);
    }

    @Override
    public String toString() {
        return "Comments{" +
                "id=" + id +
                ", groomerId=" + groomerId +
                ", userId=" + userId +
                ", title='" + title + '\'' +
                ", message='" + message + '\'' +
                ", rating=" + rating +
                '}';
    }
}
