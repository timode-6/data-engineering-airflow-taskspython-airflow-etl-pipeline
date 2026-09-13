SELECT c.name AS category, COUNT(fc.film_id) AS films
FROM category c
LEFT JOIN film_category fc ON fc.category_id = c.category_id
GROUP BY c.category_id, c.name
ORDER BY films DESC, c.name;


SELECT a.actor_id, a.first_name, a.last_name, COUNT(*) AS rentals
FROM actor a
JOIN film_actor fa ON fa.actor_id = a.actor_id
JOIN inventory i ON i.film_id = fa.film_id
JOIN rental r ON r.inventory_id = i.inventory_id
GROUP BY a.actor_id, a.first_name, a.last_name
ORDER BY rentals DESC, a.actor_id
LIMIT 10;


SELECT c.name AS category, SUM(p.amount) AS revenue
FROM category c
JOIN film_category fc ON fc.category_id = c.category_id
JOIN inventory i ON i.film_id = fc.film_id
JOIN rental r ON r.inventory_id = i.inventory_id
JOIN payment p ON p.rental_id = r.rental_id
GROUP BY c.category_id, c.name
ORDER BY revenue DESC
LIMIT 1;


SELECT f.film_id, f.title
FROM film f
WHERE NOT EXISTS (SELECT 1 FROM inventory i WHERE i.film_id = f.film_id)
ORDER BY f.title;


SELECT a.actor_id, a.first_name, a.last_name, COUNT(*) AS films
FROM actor a
JOIN film_actor fa ON fa.actor_id = a.actor_id
JOIN film_category fc ON fc.film_id = fa.film_id
JOIN category c ON c.category_id = fc.category_id
WHERE c.name = 'Children'
GROUP BY a.actor_id, a.first_name, a.last_name
ORDER BY films DESC
FETCH FIRST 3 ROWS WITH TIES;


SELECT ci.city, COUNT(*) FILTER (WHERE cu.active = 1) AS active_customers, COUNT(*) FILTER (WHERE cu.active = 0) AS inactive_customers, COUNT(*) AS total_customers
FROM city ci
JOIN address a ON a.city_id = ci.city_id
JOIN customer cu ON cu.address_id = a.address_id
GROUP BY ci.city_id, ci.city
ORDER BY inactive_customers DESC, ci.city;


WITH rental_hours AS (
    SELECT c.name AS category, ci.city, EXTRACT(EPOCH FROM (r.return_date - r.rental_date)) / 3600.0 AS hours
    FROM rental r
    JOIN inventory i ON i.inventory_id = r.inventory_id
    JOIN film_category fc ON fc.film_id = i.film_id
    JOIN category c ON c.category_id = fc.category_id
    JOIN customer cu ON cu.customer_id = r.customer_id
    JOIN address a ON a.address_id = cu.address_id
    JOIN city ci ON ci.city_id = a.city_id
    WHERE r.return_date IS NOT NULL
),
per_group AS (
    SELECT 'cities starting with "a"' AS city_group, category, SUM(hours) AS total_hours
    FROM rental_hours
    WHERE city ILIKE 'a%'
    GROUP BY category

    UNION ALL

    SELECT 'cities containing "-"' AS city_group, category, SUM(hours) AS total_hours
    FROM rental_hours
    WHERE city LIKE '%-%'
    GROUP BY category
),
ranked AS (
    SELECT city_group, category, total_hours, ROW_NUMBER() OVER (PARTITION BY city_group 
    ORDER BY total_hours DESC) AS rn
    FROM per_group
)
SELECT city_group, category, ROUND(total_hours::numeric, 2) AS total_rental_hours
FROM ranked
WHERE rn = 1
ORDER BY city_group;
