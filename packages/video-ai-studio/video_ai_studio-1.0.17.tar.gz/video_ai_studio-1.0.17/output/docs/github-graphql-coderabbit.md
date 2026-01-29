# 5. Use GitHub GraphQL for Fine-Grained Selection

GraphQL lets you fetch only the fields you care about:

```graphql
query {
  repository(owner: "org", name: "repo") {
    pullRequest(number: 123) {
      comments(first: 50) {
        nodes {
          body
          author { login }
          createdAt
        }
      }
    }
  }
}
```
