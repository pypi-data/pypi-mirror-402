use std::collections::VecDeque;

/// Simple undirected graph represented by adjacency lists.
///
/// Vertices are 0-based indices.
#[derive(Debug, Clone)]
pub struct Graph {
    /// `adjacency[v]` is the list of neighbors of vertex `v`.
    pub adjacency: Vec<Vec<usize>>,
}

impl Graph {
    pub fn num_vertices(&self) -> usize {
        self.adjacency.len()
    }

    pub fn degree(&self, v: usize) -> usize {
        self.adjacency[v].len()
    }

    pub fn neighbors(&self, v: usize) -> &[usize] {
        &self.adjacency[v]
    }

    /// Returns the shortest path distance between two vertices, or None if disconnected.
    ///
    /// # Panics
    ///
    /// Panics if `start` or `goal` are out of bounds.
    pub fn distance(&self, start: usize, goal: usize) -> Option<usize> {
        assert!(
            start < self.num_vertices() && goal < self.num_vertices(),
            "graph indices out of range (start={start}, goal={goal}, size={})",
            self.num_vertices()
        );
        if start == goal {
            return Some(0);
        }

        let dist = self.bfs(start, Some(goal));
        match dist[goal] {
            usize::MAX => None,
            goal_dist => Some(goal_dist),
        }
    }

    /// Returns the diameter of the graph, or None if the graph is disconnected.
    pub fn diameter(&self) -> Option<usize> {
        let n = self.num_vertices();
        if n == 0 {
            return Some(0);
        }

        let mut diameter = 0usize;
        for start in 0..n {
            let dist = self.bfs_from(start)?;
            if let Some(max_for_start) = dist.into_iter().max() {
                diameter = diameter.max(max_for_start);
            }
        }
        Some(diameter)
    }

    fn bfs_from(&self, start: usize) -> Option<Vec<usize>> {
        let dist = self.bfs(start, None);
        if dist.contains(&usize::MAX) {
            return None;
        }
        Some(dist)
    }

    fn bfs(&self, start: usize, stop_at: Option<usize>) -> Vec<usize> {
        debug_assert!(
            start < self.num_vertices(),
            "graph start index out of range (start={start}, size={})",
            self.num_vertices()
        );

        let vertex_count = self.num_vertices();
        let mut dist = vec![usize::MAX; vertex_count];
        let mut queue = VecDeque::new();
        dist[start] = 0;
        queue.push_back(start);

        while let Some(v) = queue.pop_front() {
            let next_dist = dist[v] + 1;
            for &n in &self.adjacency[v] {
                debug_assert!(
                    n < vertex_count,
                    "graph adjacency references {n} but size is {vertex_count}"
                );
                if dist[n] != usize::MAX {
                    continue;
                }
                dist[n] = next_dist;
                if Some(n) == stop_at {
                    return dist;
                }
                queue.push_back(n);
            }
        }

        dist
    }
}

#[cfg(test)]
mod tests {
    use super::Graph;

    #[test]
    fn distances_work_on_cycle() {
        let graph = Graph {
            adjacency: vec![vec![1, 3], vec![0, 2], vec![1, 3], vec![0, 2]],
        };

        assert_eq!(graph.distance(0, 0), Some(0));
        assert_eq!(graph.distance(0, 1), Some(1));
        assert_eq!(graph.distance(0, 2), Some(2));
        assert_eq!(graph.distance(0, 3), Some(1));
        assert_eq!(graph.diameter(), Some(2));
    }

    #[test]
    fn disconnected_graph_returns_none() {
        let graph = Graph {
            adjacency: vec![vec![1], vec![0], vec![3], vec![2]],
        };

        assert_eq!(graph.distance(0, 2), None);
        assert_eq!(graph.diameter(), None);
    }
}
