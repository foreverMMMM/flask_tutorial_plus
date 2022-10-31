const like_node = document.getElementById("like");

var liked = eval(like_node.getAttribute("data-like"));
if (liked) {
    like_node.style.color = "rgb(0, 181, 229)";
}
like_node.addEventListener("click", handleLikeClick, false);

function handleLikeClick() {
    liked = !liked;
    const likeCountNode = document.getElementById("like-count");
    this.style.color = liked ? "rgb(0, 181, 229)" : "black";
    let likeCount = parseInt(likeCountNode.innerText);
    if (liked) {
        likeCountNode.innerText =  (likeCount + 1);
    }else {
        likeCountNode.innerText =  (likeCount - 1);
    }
    doLike();
}

function doLike() {
    const articleId = document.getElementById("article-id").value;
    axios({
        method: "post",
        url: "/post/like",
        data: {
            id: parseInt(articleId),
            type: liked ? 1 : 0
        }
    })
        .then(function (resp) {
            // 待实现
            console.log(resp.data);
            const likeCountNode = document.getElementById("like-count");
            likeCountNode.innerText = resp.data.count;
        })
        .catch(function (error) {
            console.log(error);
        })
}
