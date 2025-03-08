// examples/scala/ReliableTransmission.scala
package services

import scala.concurrent.{Future, ExecutionContext}
import scala.util.{Success, Failure}

/**
 * Object that provides reliable data transmission functionality.
 * Includes mechanisms for sending and receiving data with retry logic.
 */
object ReliableTransmission {
  implicit val ec: ExecutionContext = ExecutionContext.global

  private val retryLimit = 5
  private val ackTimeout = 1000

  /**
   * Sends data to a peer with retry mechanism.
   *
   * @param peer The peer to send data to
   * @param data The data to send
   * @return A Future that completes when the data is sent successfully
   */
  def sendData(peer: String, data: String): Future[Unit] = {
    def attemptSend(retryCount: Int): Future[Unit] = {
      if (retryCount >= retryLimit) {
        handleTransmissionError(peer, "Retry limit reached")
        Future.failed(new Exception("Retry limit reached"))
      } else {
        // Simulate sending data to peer
        println(s"Sending data to $peer: $data")
        // Simulate waiting for acknowledgment
        Future {
          Thread.sleep(ackTimeout)
          if (scala.util.Random.nextBoolean()) {
            println(s"Acknowledgment received from $peer")
            Success(())
          } else {
            println(s"No acknowledgment from $peer, retrying...")
            Failure(new Exception("No acknowledgment"))
          }
        }.flatMap {
          case Success(_) => Future.successful(())
          case Failure(_) => attemptSend(retryCount + 1)
        }
      }
    }

    attemptSend(0)
  }

  /**
   * Receives data and processes it using the provided data handler.
   *
   * @param dataHandler A function that processes received data
   * @return A Future that completes when data is received and processed
   */
  def receiveData(dataHandler: String => Unit): Future[Unit] = Future {
    // Simulate receiving data
    val data = "Received data"
    println(data)
    dataHandler(data)
    // Simulate sending acknowledgment
    println("Sending acknowledgment")
  }

  /**
   * Handles transmission errors by logging them.
   *
   * @param peer The peer that had a transmission error
   * @param reason The reason for the error
   */
  def handleTransmissionError(peer: String, reason: String): Unit = {
    println(s"Transmission error with peer $peer: $reason")
  }
}