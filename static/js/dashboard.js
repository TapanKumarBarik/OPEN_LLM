fetch("/dashboard", {
  headers: {
    Authorization: `Bearer ${localStorage.getItem("access_token")}`,
  },
});
