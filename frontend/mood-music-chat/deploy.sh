BUCKET_NAME=""
DISTRIBUTION_ID=""

aws s3 sync dist/ s3://$BUCKET_NAME/ --delete --cache-control "public,max-age=31536000,immutable" --exclude "*.html"
aws s3 sync dist/ s3://$BUCKET_NAME/ --delete --cache-control "public,max-age=0,must-revalidate" --include "*.html"
aws cloudfront create-invalidation --distribution-id $DISTRIBUTION_ID --paths "/*"