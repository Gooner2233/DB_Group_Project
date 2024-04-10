import mysql.connector

# Establish connection to the database
conn = mysql.connector.connect(
    host="localhost",
    user="root",
    password="dagworlander@0911",
    database="projectDB"
)

# Create a cursor object
cursor = conn.cursor()

# Define the necissary inputs
assignment_name, crs_num = "Mid Term", 102  # Inputs For Q.4,9
course_to_match = "Physics Lecture I" # Input for Q.5,6
crs_for_new_task, task_to_add, weight_to_add = 104, "Lab Report II", 20 #Input for Q.7
task_id_to_adjust_weight, second_task_id_to_adjust_weight, crs_to_adjust_num, new_weight= 5, 4, 104, 12.5  # Inputs For Q.8
assignment_name_just_qs, crs_num_for_qs = "Homework 3", 101  # Inputs For Q.10
student_name, crs_to_grade, cat_to_drop = "McArthur", "Calculus II", 'Homework' # Inputs For Q.11,12


# Define queries to calculate average, highest, and lowest scores
q4_queries = [
    """
    SELECT AVG(TASK_RAW_POINTS) AS AverageScore
    FROM GRADING_CATEGORIES
    WHERE TASK_NAME = %s AND COURSE_NUM = %s 
    """,
    """
    SELECT MAX(TASK_RAW_POINTS) AS HighestScore
    FROM GRADING_CATEGORIES
    WHERE TASK_NAME = %s AND COURSE_NUM = %s 
    """,
    """
    SELECT MIN(TASK_RAW_POINTS) AS LowestScore
    FROM GRADING_CATEGORIES
    WHERE TASK_NAME = %s AND COURSE_NUM = %s 
    """
]

# Initialize lists to store results
q4_results = []

# Execute queries and store results
for query in q4_queries:
    cursor.execute(query, (assignment_name, crs_num))
    result = cursor.fetchone()[0]
    q4_results.append(result)

# Repeat for the other questions
q5_query = """
    SELECT STUD_LNAME
    FROM GRADEBOOK
    WHERE COURSE_NAME = %s
"""

# Execute query and store result
cursor.execute(q5_query, (course_to_match,))
q5_result = cursor.fetchall()  # fetch all results

q6_query = """
SELECT s.STUD_LNAME, gc.TASK_NAME, gc.TASK_RAW_POINTS
FROM GRADING_CATEGORIES gc
JOIN STUDENT s ON gc.STUD_ID= s.STUD_ID
WHERE gc.COURSE_NUM = (
    SELECT COURSE_NUM
    FROM COURSE_CATALOGUE
    WHERE COURSE_NAME = %s
)
"""

# Execute query and store result
cursor.execute(q6_query, (course_to_match,))
q6_result = cursor.fetchall()  # fetch all results

q7_query = """
INSERT INTO GRADING_CATEGORIES (task_id, course_num, stud_id, task_name, task_raw_points, task_weight)
SELECT 
    IFNULL((SELECT MAX(TASK_ID) FROM GRADING_CATEGORIES WHERE course_num = %s), 0) + 1,
    %s,
    gb.stud_id,
    %s,
    NULL,
    %s
FROM GRADEBOOK gb
WHERE gb.course_num = %s;
"""

# Execute query and store result
cursor.execute(q7_query, (crs_for_new_task, crs_for_new_task, task_to_add, weight_to_add, crs_for_new_task))
conn.commit()

q8_query = """
UPDATE GRADING_CATEGORIES
SET TASK_WEIGHT = 
    CASE
        WHEN TASK_ID = %s AND COURSE_NUM = %s THEN %s
        WHEN TASK_ID = %s AND COURSE_NUM = %s THEN %s
        ELSE TASK_WEIGHT
    END
;
"""
# Execute query and store result
cursor.execute(q8_query, (task_id_to_adjust_weight,
                           crs_to_adjust_num, new_weight,
                           second_task_id_to_adjust_weight,
                           crs_to_adjust_num, new_weight,))

q9_query = """
UPDATE GRADING_CATEGORIES
SET TASK_RAW_POINTS = TASK_RAW_POINTS + 2
WHERE TASK_NAME = %s AND COURSE_NUM = %s
"""
# Execute query to add 2 points to the score of each student on the assignment
cursor.execute(q9_query, (assignment_name, crs_num))
conn.commit()

# Define the query to select STUD_ID of students whose last name contains 'Q'
select_students_query = """
SELECT s.STUD_ID
FROM STUDENT s
WHERE s.STUD_LNAME LIKE '%q%'
"""

try:
    # Execute the query to select STUD_ID of eligible students
    cursor.execute(select_students_query)
    eligible_students = cursor.fetchall()
    
    # Define the query to update scores for eligible students
    update_scores_query = """
    UPDATE GRADING_CATEGORIES
    SET TASK_RAW_POINTS = TASK_RAW_POINTS + 2
    WHERE STUD_ID = %s
      AND TASK_NAME = %s
      AND COURSE_NUM = %s
    """
    
    # Iterate over eligible students and update their scores
    for student in eligible_students:
        cursor.execute(update_scores_query, (student[0], assignment_name_just_qs, crs_num_for_qs))
    
    # Commit the transaction
    conn.commit()

except Exception as e:
    # Rollback changes if an error occurs
    conn.rollback()
    print("Error:", e)

# Define the query to retrieve all scores and weights for the student
q11_query = """
SELECT gc.TASK_RAW_POINTS, gc.TASK_WEIGHT
FROM GRADING_CATEGORIES gc
JOIN STUDENT s ON gc.STUD_ID = s.STUD_ID
WHERE s.STUD_LNAME = %s
  AND gc.COURSE_NUM = (SELECT COURSE_NUM FROM COURSE_CATALOGUE WHERE COURSE_NAME = %s)
"""

# Execute the query to retrieve scores and weights for the student
cursor.execute(q11_query, (student_name, crs_to_grade))
student_scores = cursor.fetchall()

# Calculate the total weighted score for the student
total_weighted_score = sum(score * weight / 100 for score, weight in student_scores)

# Define the grading scale
grading_scale = {
    'A': 90,
    'B': 80,
    'C': 70,
    'D': 60,
    'F': 0
}
calculated_grade = next((grade for grade, threshold in grading_scale.items() if total_weighted_score >= threshold), 'F')

# Define the query to retrieve scores and weights for the student, excluding the lowest score for tasks with "Homework" in the name
q12_query = """
SELECT gc.TASK_ID, gc.TASK_RAW_POINTS, gc.TASK_WEIGHT, gc.TASK_NAME
FROM GRADING_CATEGORIES gc
JOIN STUDENT s ON gc.STUD_ID = s.STUD_ID
WHERE s.STUD_LNAME = %s
  AND gc.COURSE_NUM = (SELECT COURSE_NUM FROM COURSE_CATALOGUE WHERE COURSE_NAME = %s)
"""

# Execute the query to retrieve scores and weights for the student
cursor.execute(q12_query, (student_name, crs_to_grade))
student_scores_all = cursor.fetchall()

# Exclude the lowest score for each task with "Homework" in the name
excluded_homework, min_score, excl_weight = (), 101, 0
for task_id, score, weight, task_name in student_scores_all:
    if cat_to_drop in task_name and score<min_score:
        excluded_homework = (task_id, score, weight, task_name)
        min_score, excl_weight = score, weight

#Omit the lowest grade for this assignment
student_scores_all.remove(excluded_homework)

weight_to_increment = excl_weight/len(student_scores_all)
total_weighted_score_excl_lowest = 0
for task_id, score, weight, task_name in student_scores_all:
    total_weighted_score_excl_lowest+=score*((weight+weight_to_increment)/100)

calculated_grade_excl_lowest = next((grade for grade, threshold in grading_scale.items() if total_weighted_score_excl_lowest >= threshold), 'F')

# Print results
print("Problem 4. Avg/High/Low for assignment", assignment_name, "in course ", str(crs_num) + ":")
print("Average Score:", q4_results[0])
print("Highest Score:", q4_results[1])
print("Lowest Score:", q4_results[2],'\n')

print("Problem 5. All students who take", str(course_to_match) + ":")
for row in q5_result:
    print(row[0])

print("\nProblem 6. All raw points for each assignment for students who take", str(course_to_match) + ":")
for row in q6_result:
    print("Student:", row[0], "task:", row[1], ", Raw Points:", row[2])

print("\nProblem 7 performed (Screenshot can be found in Doc) and task", task_to_add, "added with weight", weight_to_add, "%")

print("\nProblem 8: Task weights for course", crs_to_adjust_num, "have been updated! Check Screenshots in Doc for proof.")

print("\nProblem 9: 2 points added to everyone's grades for assignment:", assignment_name + ". Check Screenshots in Doc for proof.")

# Print results
print("\nProblem 10: scores updated successfully for the following students with q's in their name:")
for student in eligible_students:
    print("Student ID:", student[0], "Assignment:", assignment_name_just_qs, "Course:", crs_num_for_qs)

print("\nProblem 11: calculated grade for student", student_name, " for course", crs_to_grade, " is: ", calculated_grade, "and a numerical final grade of:", str(total_weighted_score) + "%")

print("\nProblem 12: calculated grade for student", student_name, " for course", crs_to_grade, " with lowest score dropped is: ", calculated_grade_excl_lowest, "and a numerical final grade of:", str(total_weighted_score_excl_lowest) + "%")

# Close cursor and connection
cursor.close()
conn.close()