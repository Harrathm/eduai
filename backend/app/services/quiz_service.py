"""
Quiz Service - Auto-grading quiz attempts
"""

from datetime import datetime, timezone
from typing import List, Dict, Any, Optional
from sqlalchemy.orm import Session

from app.models import Quiz, QuizQuestion, QuizOption, QuizAttempt, QuizAnswer


class QuizService:
    """Handle quiz operations and auto-grading"""
    
    def __init__(self, db: Session):
        self.db = db
    
    def start_attempt(self, quiz_id: int, student_id: int) -> QuizAttempt:
        """Start a new quiz attempt"""
        quiz = self.db.query(Quiz).filter(Quiz.id == quiz_id).first()
        if not quiz:
            raise ValueError("Quiz not found")
        
        # Check attempts limit
        if quiz.max_attempts:
            existing = self.db.query(QuizAttempt).filter(
                QuizAttempt.quiz_id == quiz_id,
                QuizAttempt.student_id == student_id,
                QuizAttempt.status == "completed"
            ).count()
            
            if existing >= quiz.max_attempts:
                raise ValueError("Maximum attempts reached")
        
        # Create attempt
        attempt = QuizAttempt(
            quiz_id=quiz_id,
            student_id=student_id,
            status="in_progress"
        )
        self.db.add(attempt)
        self.db.commit()
        self.db.refresh(attempt)
        
        return attempt
    
    def submit_attempt(self, attempt_id: int, answers: List[Dict[str, Any]]) -> QuizAttempt:
        """Submit quiz attempt and grade automatically"""
        attempt = self.db.query(QuizAttempt).filter(QuizAttempt.id == attempt_id).first()
        if not attempt:
            raise ValueError("Attempt not found")
        
        if attempt.status != "in_progress":
            raise ValueError("Attempt already submitted")
        
        quiz = self.db.query(Quiz).filter(Quiz.id == attempt.quiz_id).first()
        
        correct_count = 0
        total_points = 0
        earned_points = 0
        total_count = len(answers)
        
        for answer_data in answers:
            question_id = answer_data.get("question_id")
            selected_ids = answer_data.get("selected_option_ids", [])
            text_answer = answer_data.get("text_answer")
            
            question = self.db.query(QuizQuestion).filter(
                QuizQuestion.id == question_id
            ).first()
            
            if not question:
                continue
            
            # Create answer record
            answer = QuizAnswer(
                attempt_id=attempt.id,
                question_id=question_id,
                selected_option_ids=selected_ids,
                text_answer=text_answer
            )
            self.db.add(answer)
            
            # Auto-grade
            if question.question_type in ["mcq", "multi", "truefalse"]:
                # Get correct option IDs
                correct_options = self.db.query(QuizOption).filter(
                    QuizOption.question_id == question_id,
                    QuizOption.is_correct == True
                ).all()
                correct_ids = set(o.id for o in correct_options)
                selected_set = set(selected_ids)
                
                # Check correctness
                if question.question_type == "mcq":
                    is_correct = len(selected_set) == 1 and selected_set == correct_ids
                else:  # multi
                    is_correct = selected_set == correct_ids
                
                answer.is_correct = is_correct
                answer.points_awarded = question.points if is_correct else 0
                
                if is_correct:
                    correct_count += 1
                
                earned_points += answer.points_awarded
            else:
                # Short answer - would use AI in production
                answer.points_awarded = 0
            
            total_points += question.points
        
        # Update attempt
        attempt.status = "completed"
        attempt.completed_at = datetime.now(timezone.utc)
        attempt.graded_at = datetime.now(timezone.utc)
        attempt.total_count = total_count
        attempt.correct_count = correct_count
        attempt.score = earned_points
        attempt.score_percent = (earned_points / total_points * 100) if total_points > 0 else 0
        attempt.passed = attempt.score_percent >= quiz.passing_score_percent
        
        self.db.commit()
        self.db.refresh(attempt)
        
        return attempt
    
    def get_quiz_for_player(self, quiz_id: int, student_id: int) -> dict:
        """Get quiz data for player (without correct answers)"""
        quiz = self.db.query(Quiz).filter(Quiz.id == quiz_id).first()
        if not quiz:
            raise ValueError("Quiz not found")
        
        questions = self.db.query(QuizQuestion).filter(
            QuizQuestion.quiz_id == quiz_id
        ).order_by(QuizQuestion.order_index).all()
        
        questions_data = []
        for q in questions:
            options = self.db.query(QuizOption).filter(
                QuizOption.question_id == q.id
            ).order_by(QuizOption.order_index).all()
            
            # Randomize if needed
            if quiz.shuffle_options:
                import random
                random.shuffle(options)
            
            questions_data.append({
                "id": q.id,
                "question_text": q.question_text,
                "question_type": q.question_type,
                "points": q.points,
                "options": [
                    {
                        "id": o.id,
                        "text": o.option_text
                    }
                    for o in options
                ]
            })
        
        return {
            "id": quiz.id,
            "title": quiz.title,
            "description": quiz.description,
            "time_limit_seconds": quiz.time_limit_seconds,
            "passing_score_percent": quiz.passing_score_percent,
            "show_results": quiz.show_results,
            "questions": questions_data
        }