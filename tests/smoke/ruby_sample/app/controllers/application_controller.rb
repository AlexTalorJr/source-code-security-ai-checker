class ApplicationController < ActionController::Base
  def index
    query = "SELECT * FROM users WHERE id = #{params[:id]}"
  end
end
